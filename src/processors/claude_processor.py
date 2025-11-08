"""
Procesador de historias clínicas usando Claude API (Anthropic).

Convierte texto extraído en estructuras validadas usando LLM.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from anthropic import Anthropic
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.schemas import HistoriaClinicaEstructurada
from src.config.settings import get_settings
from src.processors.prompts import get_extraction_prompt, get_extraction_prompt_cached
from src.processors.validators import validate_historia_completa
from src.utils.helpers import safe_json_loads
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Lista de términos que NO son diagnósticos (nombres de exámenes/procedimientos/hallazgos normales)
INVALID_DIAGNOSIS_TERMS = [
    # Exámenes/procedimientos
    'audiometr', 'rayos x', 'rayos-x', 'rx ', 'rx.', 'laboratorio',
    'electrocardiograma', 'ecg', 'ekg', 'examen', 'evaluación',
    'evaluacion', 'control', 'toma de', 'prueba', 'espirometr',
    'optometr', 'visiometr', 'hemograma', 'glicemia', 'colesterol',
    'creatinina', 'parcial de orina', 'coprológico', 'coprologico',
    'ecografía', 'ecografia', 'resonancia', 'tomografía', 'tomografia',
    'radiografía', 'radiografia', 'laboratorios', 'paraclínicos',
    'paraclinicos', 'análisis', 'analisis',

    # Hallazgos normales / sin enfermedad
    'normal', 'sin hallazgos', 'examen ocupacional', 'control rutinario',
    'audicion normal', 'vision normal', 'dentro de limites normales',
    'sin alteraciones', 'sin patologia', 'sin anormalidades'
]


def filter_invalid_diagnoses(diagnosticos: list[dict]) -> list[dict]:
    """
    Filtra diagnósticos que en realidad son:
    - Nombres de exámenes/procedimientos
    - Hallazgos normales
    - Contactos administrativos

    Args:
        diagnosticos: Lista de diagnósticos extraídos

    Returns:
        list[dict]: Diagnósticos válidos (filtrados)
    """
    if not diagnosticos:
        return []

    valid_diagnosticos = []

    for diag in diagnosticos:
        descripcion = diag.get('descripcion', '')
        codigo = diag.get('codigo_cie10', '')

        if not descripcion:
            continue

        descripcion_lower = descripcion.lower().strip()

        # Verificar si contiene algún término inválido
        is_invalid = any(
            term in descripcion_lower
            for term in INVALID_DIAGNOSIS_TERMS
        )

        # Caso especial: códigos de audición con descripción "normal"
        # Ejemplo: H90.9 con descripción "audición normal bilateral"
        if 'normal' in descripcion_lower and not is_invalid:
            # Si la descripción dice "normal", es hallazgo normal, no diagnóstico
            is_invalid = True
            logger.debug(
                f"Diagnóstico filtrado (hallazgo normal): '{descripcion}' ({codigo})"
            )

        if not is_invalid:
            valid_diagnosticos.append(diag)
        else:
            logger.debug(
                f"Diagnóstico filtrado: '{descripcion}' ({codigo})"
            )

    logger.debug(
        f"Filtrado de diagnósticos: {len(diagnosticos)} → {len(valid_diagnosticos)}"
    )

    return valid_diagnosticos


# Grupos de tokens genéricos para detección de recomendaciones no específicas
GENERIC_TOKEN_GROUPS = [
    # EPP genérico
    (['uso', 'epp'], []),
    (['elementos', 'proteccion', 'personal'], []),
    (['uso', 'adecuado', 'elementos'], []),

    # Estilo de vida
    (['habitos', 'saludable'], []),
    (['estilo', 'vida', 'saludable'], []),
    (['continuar', 'habitos'], []),

    # Ejercicio genérico
    (['ejercicio', 'fisico'], []),
    (['150', 'minutos'], ['semana']),
    (['actividad', 'fisica', 'regular'], []),

    # Fotoprotección genérica
    (['fotoproteccion'], []),
    (['proteccion', 'solar'], []),
    (['uso', 'regular', 'fotoproteccion'], []),

    # Seguridad vial genérica
    (['seguridad', 'vial'], []),
    (['apto', 'conduccion'], []),

    # Pausas
    (['pausas', 'activas'], []),
    (['pausas', 'laborales'], []),

    # Postura
    (['buena', 'postura'], []),
    (['higiene', 'postural'], []),

    # Hidratación
    (['hidratacion'], []),
    (['consumo', 'agua'], []),
]


def normalize_text_for_comparison(text: str) -> str:
    """
    Normaliza texto para comparación: lowercase, sin tildes, sin dobles espacios.

    Args:
        text: Texto a normalizar

    Returns:
        str: Texto normalizado
    """
    import unicodedata
    text = text.lower().strip()
    # Remover tildes
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Remover dobles espacios
    text = ' '.join(text.split())
    return text


def contains_token_group(text_normalized: str, required_tokens: list, optional_tokens: list) -> bool:
    """
    Verifica si el texto contiene un grupo de tokens requeridos.

    Args:
        text_normalized: Texto normalizado
        required_tokens: Tokens que deben estar presentes
        optional_tokens: Tokens opcionales (mejoran coincidencia)

    Returns:
        bool: True si contiene todos los tokens requeridos
    """
    # Todos los tokens requeridos deben estar presentes
    has_all_required = all(token in text_normalized for token in required_tokens)

    if not has_all_required:
        return False

    # Si hay tokens opcionales, al menos uno debe estar presente (mejora precisión)
    if optional_tokens:
        has_optional = any(token in text_normalized for token in optional_tokens)
        return has_optional

    return True


def filter_generic_recommendations(recomendaciones: list[dict]) -> list[dict]:
    """
    Filtra recomendaciones genéricas usando detección por grupos de tokens.

    Cambiado de matching literal a detección por combinaciones de términos
    para capturar variantes como:
    - "Uso adecuado de los elementos de protección personal"
    - "Ejercicio físico regularmente al menos 150 minutos"
    - "Continuar hábitos y estilos de vida saludable"

    Args:
        recomendaciones: Lista de recomendaciones extraídas

    Returns:
        list[dict]: Recomendaciones específicas (filtradas)
    """
    if not recomendaciones:
        return []

    filtered = []

    for rec in recomendaciones:
        descripcion = rec.get('descripcion', '')
        if not descripcion:
            continue

        desc_normalized = normalize_text_for_comparison(descripcion)

        # Verificar si contiene algún grupo de tokens genéricos
        is_generic = False
        for required_tokens, optional_tokens in GENERIC_TOKEN_GROUPS:
            if contains_token_group(desc_normalized, required_tokens, optional_tokens):
                is_generic = True
                logger.debug(
                    f"Recomendación genérica filtrada (tokens: {required_tokens}): '{descripcion}'"
                )
                break

        if not is_generic:
            filtered.append(rec)

    logger.debug(
        f"Filtrado de recomendaciones: {len(recomendaciones)} → {len(filtered)}"
    )

    return filtered


def deduplicate_recommendations(recomendaciones: list[dict]) -> list[dict]:
    """
    Elimina recomendaciones duplicadas basándose en descripción normalizada.

    Args:
        recomendaciones: Lista de recomendaciones

    Returns:
        list[dict]: Recomendaciones sin duplicados
    """
    if not recomendaciones:
        return []

    seen_descriptions = set()
    deduplicated = []

    for rec in recomendaciones:
        descripcion = rec.get('descripcion', '')
        if not descripcion:
            continue

        desc_normalized = normalize_text_for_comparison(descripcion)

        if desc_normalized not in seen_descriptions:
            seen_descriptions.add(desc_normalized)
            deduplicated.append(rec)
        else:
            logger.debug(f"Recomendación duplicada eliminada: '{descripcion}'")

    if len(deduplicated) < len(recomendaciones):
        logger.debug(
            f"Deduplicación de recomendaciones: {len(recomendaciones)} → {len(deduplicated)}"
        )

    return deduplicated


def reclassify_epp_as_recommendations(historia_dict: dict) -> dict:
    """
    Limpia campo restricciones_especificas si solo contiene uso de EPP.

    Restricciones deben ser LIMITACIONES de actividad, no uso de EPP.
    El uso de EPP debe ir en recomendaciones.

    Args:
        historia_dict: Diccionario con la historia clínica

    Returns:
        dict: Historia con restricciones_especificas corregido
    """
    import re

    restricciones = historia_dict.get('restricciones_especificas', '')

    if not restricciones:
        return historia_dict

    # Patrones que indican EPP (no son restricciones reales)
    epp_patterns = [
        r'uso de\s+(?:lentes|gafas|anteojos)',
        r'uso de\s+protector(?:es)?\s+auditivo',
        r'uso de\s+(?:elementos|equipos)\s+de\s+protecci[oó]n',
        r'uso de\s+epp',
        r'uso de\s+guantes',
        r'uso de\s+casco',
        r'uso de\s+mascarilla',
        r'uso de\s+protector\s+solar',
        r'uso\s+(?:permanente|ocasional)\s+de'
    ]

    restricciones_lower = restricciones.lower()

    # Verificar si hay EPP
    has_epp = any(re.search(pattern, restricciones_lower) for pattern in epp_patterns)

    # Verificar si hay restricciones REALES (limitaciones de actividad)
    restricciones_reales_patterns = [
        r'no\s+levantar',
        r'no\s+cargar',
        r'no\s+trabajar\s+en\s+altura',
        r'evitar\s+exposici[oó]n\s+a',
        r'no\s+conducir',
        r'no\s+trabajar\s+en\s+turno',
        r'no\s+realizar\s+movimientos',
        r'no\s+permanecer\s+de\s+pie',
        r'limitaci[oó]n\s+para',
        r'restricci[oó]n\s+para',
        r'evitar\s+movimientos',
        r'evitar\s+actividades'
    ]

    has_real_restrictions = any(
        re.search(pattern, restricciones_lower)
        for pattern in restricciones_reales_patterns
    )

    # Si solo hay EPP y NO hay restricciones reales, limpiar el campo
    if has_epp and not has_real_restrictions:
        logger.debug(
            f"restricciones_especificas contenía solo EPP (no restricciones reales), "
            f"limpiando campo. Valor original: '{restricciones[:100]}...'"
        )
        historia_dict['restricciones_especificas'] = None

    return historia_dict


# Términos de negación para antecedentes
NEGATION_TERMS = [
    "niega",
    "sin antecedentes",
    "no refiere antecedentes",
    "no refiere antecedentes de importancia",
    " no",  # Para patrones como "Vértigo: NO", "Fobia: NO"
    ": no",
    "no aplica",
    "n/a",
    "sin datos",
]


def is_pure_negation(desc: str) -> bool:
    """
    Determina si una descripción de antecedente es una negación pura.

    Una negación pura es texto que solo indica ausencia de antecedentes,
    sin mencionar condiciones clínicas afirmativas.

    Detecta patrones como:
    - "NIEGA"
    - "Sin antecedentes"
    - "Vértigo: NO"
    - "Fobia: NO"
    - "No aplica"

    Args:
        desc: Descripción del antecedente

    Returns:
        bool: True si es negación pura, False si contiene información clínica afirmativa
    """
    if not desc:
        return False

    text = normalize_text_for_comparison(desc)

    # Descripciones muy largas suelen incluir más contexto: no son negación pura
    if len(text) > 80:
        return False

    # Patrones de negación
    negation_hit = any(term in text for term in NEGATION_TERMS)

    # Patrón específico: "término: no" (muy corto, solo niega)
    # Ejemplo: "Vertigo: NO" → len ~12, tiene "no", no tiene afirmación
    if len(text) < 30 and ' no' in text:
        negation_hit = True

    # Si no hay hit de negación, no es negación pura
    if not negation_hit:
        return False

    # Si menciona alguna condición concreta AFIRMATIVA, no es solo negación
    # Keywords que indican antecedente REAL (no solo "Diabetes: NO")
    clinical_affirmative_keywords = [
        "diagnostico", "desde", "hace", "años", "meses",
        "tratamiento con", "medicamento", "cirugia de", "fractura de",
        "hospitalizacion por", "episodio de"
    ]
    has_affirmative_clinical = any(k in text for k in clinical_affirmative_keywords)

    # Es negación pura si: tiene negación AND NO tiene afirmación clínica
    return negation_hit and not has_affirmative_clinical


def consolidate_negation_antecedentes(antecedentes: list[dict]) -> list[dict]:
    """
    Elimina antecedentes que son solo negaciones genéricas.

    Reglas:
    1. Si TODOS los antecedentes son negaciones puras → devuelve lista vacía
       (se interpreta como "sin antecedentes relevantes")
    2. Si hay mezcla → elimina solo las negaciones puras, conserva los específicos

    No genera texto sintético, solo filtra lo que ya existe.

    Args:
        antecedentes: Lista de antecedentes extraídos

    Returns:
        list[dict]: Antecedentes filtrados (puede ser lista vacía)
    """
    if not antecedentes:
        return []

    cleaned = []
    saw_negation = False

    for ant in antecedentes:
        desc = (ant.get("descripcion") or "").strip()
        if is_pure_negation(desc):
            saw_negation = True
            logger.debug(f"Antecedente con negación pura filtrado: '{desc}'")
            continue
        cleaned.append(ant)

    # Si solo había negaciones genéricas → lista vacía
    if saw_negation and not cleaned:
        logger.debug(
            f"Todos los antecedentes eran negaciones puras, "
            f"devolviendo lista vacía (sin antecedentes relevantes)"
        )
        return []

    logger.debug(
        f"Filtrado de antecedentes: {len(antecedentes)} → {len(cleaned)}"
    )

    return cleaned


def summarize_normal_physical_exam(hallazgos: str) -> str:
    """
    Resume hallazgos_examen_fisico cuando no hay hallazgos patológicos.

    Criterio: Buscar SOLO términos claramente patológicos.
    "negativo/negativas" NO son patológicos (son parte de normalidad).

    Reglas:
    - Si NO hay palabras patológicas
    - Y el texto supera 200 caracteres
    - Entonces resumir como "sin hallazgos patológicos relevantes"

    Args:
        hallazgos: Texto de hallazgos del examen físico

    Returns:
        str: Hallazgos resumidos si aplica, original si hay hallazgos patológicos
    """
    if not hallazgos or len(hallazgos) <= 200:
        return hallazgos

    text_lower = normalize_text_for_comparison(hallazgos)

    # Indicadores de hallazgos CLARAMENTE patológicos
    # NO incluir: "negativo", "negativas", "sin", "normal" (son normalidad)
    pathologic_indicators = [
        "dolor", "masa", "hernia", "tumor", "edema",
        "inflamado", "inflamacion", "limitacion", "disminuido",
        "aumentado", "ulcera", "lesion", "fractura",
        "deformidad", "atrofia", "hipertrofia", "espasmo",
        "rigidez", "contractura", "adenopatia", "soplo",
        "arritmia", "crepitacion", "derrame"
    ]

    # Si tiene hallazgos patológicos, conservar completo
    has_pathologic = any(ind in text_lower for ind in pathologic_indicators)

    if has_pathologic:
        return hallazgos

    # Si NO hay hallazgos patológicos y es largo, resumir
    logger.debug(
        f"hallazgos_examen_fisico sin hallazgos patológicos y >200 chars, "
        f"resumiendo. Longitud original: {len(hallazgos)}"
    )
    return "Examen físico sin hallazgos patológicos relevantes"


def clean_exam_findings(examenes: list[dict]) -> list[dict]:
    """
    Limpia hallazgos_clave en exámenes según interpretación.

    Reglas:
    - Si interpretacion = "normal" → resumir hallazgos_clave
    - Si interpretacion = "alterado" o "critico" → conservar TODO

    No usa null para evitar confusión con campo faltante.

    Args:
        examenes: Lista de exámenes paraclínicos

    Returns:
        list[dict]: Exámenes con hallazgos_clave limpiados
    """
    if not examenes:
        return []

    for exam in examenes:
        interpretacion = exam.get('interpretacion')
        hallazgos = exam.get('hallazgos_clave', '')

        # Si es normal y tiene hallazgos detallados, resumir
        if interpretacion == 'normal' and hallazgos and len(hallazgos) > 50:
            logger.debug(
                f"Examen {exam.get('tipo', 'desconocido')} normal con hallazgos "
                f"detallados ({len(hallazgos)} chars), resumiendo"
            )
            exam['hallazgos_clave'] = "Todos los parámetros dentro de rangos normales"

        # Si es alterado o crítico, conservar TODO (no filtrar por ahora)

    return examenes


class ClaudeProcessor:
    """
    Procesador de historias clínicas usando Claude API.

    Toma texto extraído por Azure y retorna HistoriaClinicaEstructurada.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        """
        Inicializa el procesador de Claude.

        Args:
            api_key: API key de Anthropic (si None, usa settings)
            model: Modelo a usar (si None, usa settings)
            max_tokens: Máximo de tokens (si None, usa settings)
            temperature: Temperatura (si None, usa settings)
        """
        settings = get_settings()

        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model
        self.max_tokens = max_tokens or settings.claude_max_tokens
        self.temperature = temperature or settings.claude_temperature

        # Validar API key
        if not self.api_key or not self.api_key.startswith("sk-ant-"):
            raise ValueError(
                "Anthropic API key inválida. "
                "Verifique ANTHROPIC_API_KEY en .env"
            )

        # Crear cliente
        self.client = Anthropic(api_key=self.api_key)

        logger.info(
            f"ClaudeProcessor inicializado con modelo: {self.model}, "
            f"max_tokens: {self.max_tokens}, temperature: {self.temperature}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def process(
        self,
        texto_extraido: str,
        archivo_origen: str,
        context: Optional[Dict[str, str]] = None
    ) -> HistoriaClinicaEstructurada:
        """
        Procesa texto extraído y retorna historia clínica estructurada.

        Args:
            texto_extraido: Texto extraído por Azure Document Intelligence
            archivo_origen: Nombre del archivo PDF original
            context: Contexto adicional (empresa, fecha, etc.)

        Returns:
            HistoriaClinicaEstructurada: Historia clínica validada

        Raises:
            ValueError: Si la respuesta de Claude no es válida
            ValidationError: Si el JSON no cumple el schema Pydantic
        """
        logger.info(f"Procesando historia clínica: {archivo_origen}")

        # Preparar context
        if context is None:
            context = {}
        context["archivo_origen"] = archivo_origen

        # Obtener settings para verificar si caching está habilitado
        settings = get_settings()

        try:
            # Llamar a Claude API con o sin caching según configuración
            if settings.enable_prompt_caching:
                # Usar prompt caching para reducir costos 90%
                system_blocks, user_message = get_extraction_prompt_cached(
                    texto_extraido=texto_extraido,
                    context=context
                )

                logger.debug(
                    f"Prompt con cache generado: "
                    f"{len(system_blocks)} bloques de sistema + "
                    f"{len(user_message)} caracteres de mensaje"
                )

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_blocks,  # System blocks cacheables
                    messages=[
                        {
                            "role": "user",
                            "content": user_message  # Solo contenido variable
                        }
                    ]
                )
            else:
                # Modo sin cache (backward compatibility)
                prompt = get_extraction_prompt(
                    texto_extraido=texto_extraido,
                    context=context
                )

                logger.debug(f"Prompt sin cache generado: {len(prompt)} caracteres")

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

            # Extraer texto de la respuesta
            response_text = response.content[0].text

            logger.debug(f"Respuesta de Claude: {len(response_text)} caracteres")

            # Parsear JSON
            historia_dict = self._parse_claude_response(response_text)

            # Postprocesamiento: Filtrar diagnósticos inválidos (nombres de exámenes)
            if 'diagnosticos' in historia_dict and historia_dict['diagnosticos']:
                historia_dict['diagnosticos'] = filter_invalid_diagnoses(
                    historia_dict['diagnosticos']
                )

            # Postprocesamiento: Filtrar recomendaciones genéricas
            if 'recomendaciones' in historia_dict and historia_dict['recomendaciones']:
                historia_dict['recomendaciones'] = filter_generic_recommendations(
                    historia_dict['recomendaciones']
                )
                # Deduplicar después de filtrar genéricas
                historia_dict['recomendaciones'] = deduplicate_recommendations(
                    historia_dict['recomendaciones']
                )

            # Postprocesamiento: Reclasificar EPP mal ubicado en restricciones
            historia_dict = reclassify_epp_as_recommendations(historia_dict)

            # Postprocesamiento: Consolidar antecedentes con negaciones puras
            if 'antecedentes' in historia_dict and historia_dict['antecedentes']:
                historia_dict['antecedentes'] = consolidate_negation_antecedentes(
                    historia_dict['antecedentes']
                )

            # Postprocesamiento: Resumir hallazgos de examen físico normales
            if 'hallazgos_examen_fisico' in historia_dict and historia_dict['hallazgos_examen_fisico']:
                historia_dict['hallazgos_examen_fisico'] = summarize_normal_physical_exam(
                    historia_dict['hallazgos_examen_fisico']
                )

            # Postprocesamiento: Limpiar hallazgos_clave en exámenes normales
            if 'examenes' in historia_dict and historia_dict['examenes']:
                historia_dict['examenes'] = clean_exam_findings(
                    historia_dict['examenes']
                )

            # Agregar metadata
            historia_dict["archivo_origen"] = archivo_origen

            # Validar contra schema Pydantic
            historia = HistoriaClinicaEstructurada.model_validate(historia_dict)

            # Ejecutar validaciones adicionales
            alertas_adicionales = validate_historia_completa(historia)

            # Agregar alertas de validación
            historia.alertas_validacion.extend(alertas_adicionales)

            # Filtrar alertas innecesarias/ruido
            historia.alertas_validacion = self._filter_unnecessary_alerts(
                historia.alertas_validacion,
                historia
            )

            # Calcular confianza si no fue calculada
            if historia.confianza_extraccion == 0.0:
                historia.confianza_extraccion = self._calculate_confidence(historia)

            logger.info(
                f"Procesamiento exitoso: {len(historia.diagnosticos)} diagnósticos, "
                f"{len(historia.examenes)} exámenes, "
                f"confianza: {historia.confianza_extraccion:.2f}, "
                f"{len(historia.alertas_validacion)} alertas"
            )

            return historia

        except Exception as e:
            logger.error(f"Error procesando {archivo_origen}: {e}")
            raise

    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta de Claude y extrae el JSON.

        Args:
            response_text: Texto de respuesta de Claude

        Returns:
            dict: Diccionario con la historia clínica

        Raises:
            ValueError: Si no se puede parsear el JSON
        """
        # Intentar parseo directo
        historia_dict = safe_json_loads(response_text)

        if historia_dict is not None:
            return historia_dict

        # Intentar extraer JSON si está embebido en texto
        # Buscar entre { y }
        start = response_text.find('{')
        end = response_text.rfind('}')

        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end + 1]
            historia_dict = safe_json_loads(json_str)

            if historia_dict is not None:
                return historia_dict

        # Si todo falla, lanzar error
        logger.error(f"No se pudo parsear respuesta de Claude: {response_text[:500]}...")
        raise ValueError(
            "La respuesta de Claude no contiene JSON válido. "
            "Verifique los logs para más detalles."
        )

    def _filter_unnecessary_alerts(
        self,
        alertas: list,
        historia: HistoriaClinicaEstructurada
    ) -> list:
        """
        Filtra alertas innecesarias o de ruido administrativo.

        Alertas eliminadas:
        - Falta de EPS/ARL (dato administrativo, no clínico)
        - En consolidados: alertas de tipo_emo/aptitud faltante si ya están poblados
        - En consolidados con exámenes específicos: alertas de campos que solo aplican a HC completa

        Args:
            alertas: Lista de alertas
            historia: Historia clínica procesada

        Returns:
            list: Alertas filtradas
        """
        if not alertas:
            return []

        # Detectar si es consolidado
        historia_dict = historia.model_dump()
        archivos_consolidados = historia_dict.get('archivos_origen_consolidados', [])
        es_consolidado = bool(archivos_consolidados)

        # Si es consolidado, verificar si hay exámenes específicos en las fuentes
        tiene_examenes_especificos = False
        if es_consolidado:
            # Los archivos origen consolidados están en el JSON como metadata
            # pero no están disponibles aquí directamente
            # Asumiremos que si tipo_documento_fuente == 'hc_completa' pero
            # hay múltiples archivos, puede haber exámenes específicos consolidados
            tiene_examenes_especificos = len(archivos_consolidados) > 1

        filtered = []

        for alerta in alertas:
            should_filter = False

            # 1. Filtrar alerta de EPS/ARL faltante (administrativo, no clínico)
            if (alerta.tipo == "dato_faltante" and
                alerta.campo_afectado == "datos_empleado" and
                "EPS" in alerta.descripcion and "ARL" in alerta.descripcion):
                should_filter = True
                logger.debug(f"Alerta administrativa filtrada: {alerta.descripcion}")

            # 2. En consolidados: filtrar alertas de campos que YA están poblados
            if es_consolidado and alerta.tipo == "dato_faltante":
                # Si alerta sobre tipo_emo pero el consolidado SÍ tiene tipo_emo
                if alerta.campo_afectado == "tipo_emo" and historia.tipo_emo:
                    should_filter = True
                    logger.debug(
                        f"Alerta de consolidado filtrada (campo poblado): "
                        f"{alerta.campo_afectado}"
                    )

                # Si alerta sobre aptitud pero el consolidado SÍ tiene aptitud
                if alerta.campo_afectado == "aptitud_laboral" and historia.aptitud_laboral:
                    should_filter = True
                    logger.debug(
                        f"Alerta de consolidado filtrada (campo poblado): "
                        f"{alerta.campo_afectado}"
                    )

                # Si alerta sobre fecha_emo pero el consolidado SÍ tiene fecha_emo
                if alerta.campo_afectado == "fecha_emo" and historia.fecha_emo:
                    should_filter = True
                    logger.debug(
                        f"Alerta de consolidado filtrada (campo poblado): "
                        f"{alerta.campo_afectado}"
                    )

            # 3. Evitar alertas duplicadas por descripción similar
            # (múltiples fuentes pueden generar la misma alerta)
            if es_consolidado:
                # Si la alerta ya existe en filtered con misma descripción normalizada
                desc_normalizada = normalize_text_for_comparison(alerta.descripcion)
                ya_existe = any(
                    normalize_text_for_comparison(a.descripcion) == desc_normalizada
                    for a in filtered
                )
                if ya_existe:
                    should_filter = True
                    logger.debug(
                        f"Alerta duplicada en consolidado filtrada: {alerta.descripcion[:50]}..."
                    )

            # Conservar si no debe filtrarse
            if not should_filter:
                filtered.append(alerta)

        if len(filtered) < len(alertas):
            logger.debug(f"Alertas filtradas: {len(alertas)} → {len(filtered)}")

        return filtered

    def _calculate_confidence(self, historia: HistoriaClinicaEstructurada) -> float:
        """
        Calcula la confianza global de la extracción.

        Args:
            historia: Historia clínica procesada

        Returns:
            float: Confianza promedio (0.0 - 1.0)
        """
        confidences = []

        # Confianza de diagnósticos
        for diag in historia.diagnosticos:
            confidences.append(diag.confianza)

        # Si no hay valores, asumir confianza media
        if not confidences:
            return 0.5

        return sum(confidences) / len(confidences)

    def process_batch(
        self,
        textos: list[tuple[str, str]],
        show_progress: bool = True
    ) -> list[HistoriaClinicaEstructurada]:
        """
        Procesa múltiples historias clínicas en batch.

        Args:
            textos: Lista de tuplas (texto_extraido, archivo_origen)
            show_progress: Mostrar barra de progreso

        Returns:
            list[HistoriaClinicaEstructurada]: Historias procesadas
        """
        historias = []

        if show_progress:
            try:
                from rich.progress import Progress, SpinnerColumn, TextColumn
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                ) as progress:
                    task = progress.add_task(
                        f"Procesando {len(textos)} historias clínicas...",
                        total=len(textos)
                    )

                    for texto, archivo in textos:
                        try:
                            historia = self.process(texto, archivo)
                            historias.append(historia)
                        except Exception as e:
                            logger.error(f"Error procesando {archivo}: {e}")
                        finally:
                            progress.update(task, advance=1)
            except ImportError:
                # Fallback sin progress bar
                for texto, archivo in textos:
                    try:
                        historia = self.process(texto, archivo)
                        historias.append(historia)
                    except Exception as e:
                        logger.error(f"Error procesando {archivo}: {e}")
        else:
            for texto, archivo in textos:
                try:
                    historia = self.process(texto, archivo)
                    historias.append(historia)
                except Exception as e:
                    logger.error(f"Error procesando {archivo}: {e}")

        logger.info(
            f"Batch completado: {len(historias)}/{len(textos)} historias procesadas exitosamente"
        )

        return historias


__all__ = ["ClaudeProcessor"]
