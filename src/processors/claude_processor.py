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
from src.processors.recommendation_filters import filter_recommendations
from src.processors.alert_filters import filter_alerts
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
    Resume hallazgos_examen_fisico preservando SIEMPRE la patología.

    Lógica inteligente:
    1. Si hay ≥1 hallazgo patológico REAL → conservar solo esos + resumir resto
    2. Si todo es normal (≥3 negaciones o ratio >0.6) y >150 chars → resumen completo
    3. NUNCA perder información patológica

    Criterio de normalidad:
    - Contar negaciones explícitas: "sin X", "no X", "ausencia de", "normal", "negativas"
    - Detectar afirmaciones patológicas verificando contexto (no precedidas de negación)
    - Umbral: ≥3 negaciones o ratio_negaciones/total_palabras > 0.6

    Args:
        hallazgos: Texto de hallazgos del examen físico

    Returns:
        str: Hallazgos resumidos si aplica, original si hay hallazgos patológicos
    """
    import re

    if not hallazgos or len(hallazgos) <= 150:
        return hallazgos

    text_lower = hallazgos.lower()
    text_normalized = normalize_text_for_comparison(hallazgos)

    # Paso 1: Contar indicadores de normalidad
    negation_patterns = [
        r'\bsin\s+\w+',           # "sin adenopatías"
        r'\bno\s+\w+',            # "no masas"
        r'\bausencia\s+de',       # "ausencia de"
        r'\bnormal(?:es)?',       # "normal", "normales"
        r'\bnegativ[oa]s?',       # "negativo", "negativas"
        r'\bdentro\s+de'          # "dentro de límites"
    ]

    negation_count = sum(len(re.findall(p, text_lower, re.I)) for p in negation_patterns)
    total_palabras = len(text_normalized.split())
    ratio_negaciones = negation_count / total_palabras if total_palabras > 0 else 0

    # Paso 2: Buscar afirmaciones patológicas REALES (no precedidas de negación)
    pathologic_indicators = [
        "dolor", "masa", "hernia", "tumor", "edema",
        "inflamado", "inflamacion", "limitacion", "disminuido",
        "aumentado", "ulcera", "lesion", "fractura",
        "deformidad", "atrofia", "hipertrofia", "espasmo",
        "rigidez", "contractura", "adenopatia", "soplo",
        "arritmia", "crepitacion", "derrame"
    ]

    pathologic_findings = []
    for term in pathologic_indicators:
        # Buscar todas las ocurrencias del término
        pattern = r'\b' + term + r'\w*'
        matches = list(re.finditer(pattern, text_lower, re.I))

        for match in matches:
            # Verificar contexto: 30 caracteres antes del término
            start = max(0, match.start() - 30)
            context_before = text_lower[start:match.start()]

            # Si NO hay negación cerca → es afirmación patológica
            if not re.search(r'\b(sin|no|ausencia|niega|negativ)', context_before):
                # Extraer la frase completa (hasta el punto o nueva línea)
                sentence_start = text_lower.rfind('.', 0, match.start())
                sentence_start = sentence_start + 1 if sentence_start != -1 else 0
                sentence_end = text_lower.find('.', match.end())
                sentence_end = sentence_end if sentence_end != -1 else len(text_lower)

                pathologic_sentence = hallazgos[sentence_start:sentence_end].strip()
                if pathologic_sentence and pathologic_sentence not in pathologic_findings:
                    pathologic_findings.append(pathologic_sentence)
                break  # Ya encontramos este término como patológico

    # Paso 3: Decidir acción basada en hallazgos

    # Caso 1: Hay hallazgos patológicos → conservar solo esos + resumir resto
    if pathologic_findings:
        logger.debug(
            f"Examen físico con {len(pathologic_findings)} hallazgo(s) patológico(s), "
            f"conservando solo esos y resumiendo resto"
        )
        resultado = ". ".join(pathologic_findings)
        resultado += ". Resto de sistemas sin hallazgos patológicos relevantes."
        return resultado

    # Caso 2: Todo normal → verificar si cumple umbral para resumir
    if (negation_count >= 3 or ratio_negaciones > 0.6) and len(hallazgos) > 150:
        logger.debug(
            f"Examen físico sin hallazgos patológicos "
            f"(negaciones: {negation_count}, ratio: {ratio_negaciones:.2f}), "
            f"resumiendo. Longitud original: {len(hallazgos)}"
        )
        return "Examen físico sin hallazgos patológicos relevantes"

    # Caso 3: No cumple umbral o es corto → conservar original
    return hallazgos


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

        # Si es normal:
        if interpretacion == 'normal':
            # Caso 1: hallazgos vacíos → asignar texto estándar
            if not hallazgos or hallazgos.strip() == '':
                exam['hallazgos_clave'] = "Resultados dentro de parámetros normales"
                logger.debug(
                    f"Examen {exam.get('tipo', 'desconocido')} normal sin hallazgos, "
                    f"asignando texto estándar"
                )
            # Caso 2: hallazgos detallados (>50 chars) → resumir
            elif len(hallazgos) > 50:
                exam['hallazgos_clave'] = "Todos los parámetros dentro de rangos normales"
                logger.debug(
                    f"Examen {exam.get('tipo', 'desconocido')} normal con hallazgos "
                    f"detallados ({len(hallazgos)} chars), resumiendo"
                )
            # Caso 3: hallazgos cortos → conservar (puede ser específico)

        # Si es alterado o crítico, conservar TODO (no filtrar por ahora)

    return examenes


def validate_signos_vitales(historia_dict: dict, alertas_adicionales: list) -> dict:
    """
    Valida signos vitales contra rangos clínicos esperados.

    Si un valor está fuera de rango esperado:
    - Setear campo a None
    - Agregar alerta tipo valor_critico

    Rangos esperados (permisivos para cubrir casos clínicos válidos):
    - FC: 40-200 lpm
    - FR: 8-40 rpm
    - Temperatura: 35.0-42.0 °C
    - SpO2: 70-100%
    - Peso: 20-300 kg
    - Talla: 100-250 cm
    - IMC: 10-60

    Args:
        historia_dict: Diccionario con la historia clínica
        alertas_adicionales: Lista para agregar alertas generadas

    Returns:
        dict: Historia con signos vitales validados
    """
    if 'signos_vitales' not in historia_dict or not historia_dict['signos_vitales']:
        return historia_dict

    signos = historia_dict['signos_vitales']

    # Definir rangos esperados (min, max, unidad, nombre legible)
    validaciones = [
        ('frecuencia_cardiaca', 40, 200, 'lpm', 'Frecuencia cardíaca'),
        ('frecuencia_respiratoria', 8, 40, 'rpm', 'Frecuencia respiratoria'),
        ('temperatura', 35.0, 42.0, '°C', 'Temperatura'),
        ('saturacion_oxigeno', 70, 100, '%', 'Saturación de oxígeno'),
        ('peso_kg', 20.0, 300.0, 'kg', 'Peso'),
        ('talla_cm', 100.0, 250.0, 'cm', 'Talla'),
        ('imc', 10.0, 60.0, '', 'IMC'),
    ]

    from src.config.schemas import Alerta

    for campo, min_val, max_val, unidad, nombre in validaciones:
        valor = signos.get(campo)

        if valor is None:
            continue

        # Validar rango
        try:
            valor_num = float(valor)

            if valor_num < min_val or valor_num > max_val:
                logger.warning(
                    f"{nombre} fuera de rango esperado: {valor_num} {unidad} "
                    f"(esperado: {min_val}-{max_val}). Seteando a None."
                )

                # Setear a None
                signos[campo] = None

                # Agregar alerta
                alertas_adicionales.append(
                    Alerta(
                        tipo="valor_critico",
                        severidad="alta",
                        campo_afectado=f"signos_vitales.{campo}",
                        descripcion=f"{nombre} fuera de rango clínico esperado: {valor_num} {unidad} (esperado: {min_val}-{max_val})",
                        accion_sugerida="Verificar valor en documento original, probable error de transcripción"
                    )
                )

        except (ValueError, TypeError):
            # Si no se puede convertir a número, dejarlo pasar
            # Pydantic lo manejará
            logger.debug(f"{nombre} no es numérico: {valor}, dejando para Pydantic")
            continue

    return historia_dict


def normalize_aptitud_laboral(historia_dict: dict, alertas_adicionales: list) -> dict:
    """
    Normaliza el campo aptitud_laboral antes de validación Pydantic.

    Reglas:
    1. "aplazado" → "pendiente"
    2. Valores fuera de catálogo → "pendiente" + alerta valor_no_estandarizado

    Args:
        historia_dict: Diccionario con la historia clínica
        alertas_adicionales: Lista para agregar alertas generadas

    Returns:
        dict: Historia con aptitud_laboral normalizado
    """
    aptitud_original = historia_dict.get('aptitud_laboral')

    if not aptitud_original:
        return historia_dict

    # Catálogo válido de aptitudes
    VALID_APTITUDES = {
        "apto",
        "apto_sin_restricciones",
        "apto_con_recomendaciones",
        "apto_con_restricciones",
        "no_apto_temporal",
        "no_apto_definitivo",
        "pendiente"
    }

    # Normalizar a lowercase y quitar espacios
    aptitud_clean = str(aptitud_original).lower().strip()

    # Mapeo de variantes comunes
    APTITUD_MAPPINGS = {
        "aplazado": "pendiente",
        "aplazada": "pendiente",
        "pendiente_evaluacion": "pendiente",
        "en_evaluacion": "pendiente",
        "por_definir": "pendiente",
    }

    # Aplicar mapeo si existe
    if aptitud_clean in APTITUD_MAPPINGS:
        aptitud_normalizada = APTITUD_MAPPINGS[aptitud_clean]
        logger.info(
            f"aptitud_laboral normalizada: '{aptitud_original}' → '{aptitud_normalizada}'"
        )
        historia_dict['aptitud_laboral'] = aptitud_normalizada

        # Agregar alerta informativa
        from src.config.schemas import Alerta
        alertas_adicionales.append(
            Alerta(
                tipo="formato_incorrecto",
                severidad="baja",
                campo_afectado="aptitud_laboral",
                descripcion=f"Aptitud laboral no estándar: '{aptitud_original}' normalizada a '{aptitud_normalizada}'",
                accion_sugerida="Verificar valor original en documento fuente"
            )
        )
        return historia_dict

    # Si no está en el catálogo válido → setear "pendiente" + alerta
    if aptitud_clean not in VALID_APTITUDES:
        logger.warning(
            f"aptitud_laboral fuera de catálogo: '{aptitud_original}', "
            f"seteando a 'pendiente'"
        )
        historia_dict['aptitud_laboral'] = "pendiente"

        # Agregar alerta de valor no estandarizado
        from src.config.schemas import Alerta
        alertas_adicionales.append(
            Alerta(
                tipo="formato_incorrecto",
                severidad="media",
                campo_afectado="aptitud_laboral",
                descripcion=f"Aptitud laboral no reconocida: '{aptitud_original}'. Se estableció como 'pendiente'",
                accion_sugerida="Revisar documento para determinar aptitud laboral correcta"
            )
        )

    return historia_dict


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

            # Limpieza defensiva: Eliminar campos deprecados (eps, area)
            if 'datos_empleado' in historia_dict and historia_dict['datos_empleado']:
                historia_dict['datos_empleado'].pop('eps', None)
                historia_dict['datos_empleado'].pop('area', None)

            # Postprocesamiento: Filtrar diagnósticos inválidos (nombres de exámenes)
            if 'diagnosticos' in historia_dict and historia_dict['diagnosticos']:
                historia_dict['diagnosticos'] = filter_invalid_diagnoses(
                    historia_dict['diagnosticos']
                )

            # Postprocesamiento: Filtrar recomendaciones genéricas (NUEVO filtro centralizado)
            if 'recomendaciones' in historia_dict and historia_dict['recomendaciones']:
                historia_dict['recomendaciones'] = filter_recommendations(
                    historia_dict['recomendaciones'],
                    historia_dict
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

            # Pre-procesamiento: Validaciones ANTES de Pydantic
            alertas_preprocesamiento = []

            # 1. Validar signos vitales con rangos esperados
            historia_dict = validate_signos_vitales(historia_dict, alertas_preprocesamiento)

            # 2. Normalizar aptitud_laboral
            historia_dict = normalize_aptitud_laboral(historia_dict, alertas_preprocesamiento)

            # Validar contra schema Pydantic
            historia = HistoriaClinicaEstructurada.model_validate(historia_dict)

            # Agregar alertas de pre-procesamiento
            historia.alertas_validacion.extend(alertas_preprocesamiento)

            # Ejecutar validaciones adicionales
            alertas_adicionales = validate_historia_completa(historia)

            # Agregar alertas de validación
            historia.alertas_validacion.extend(alertas_adicionales)

            # Filtrar alertas innecesarias/ruido (NUEVO filtro centralizado)
            historia.alertas_validacion = filter_alerts(
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
