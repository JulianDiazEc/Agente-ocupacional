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


# Lista de términos que NO son diagnósticos (nombres de exámenes/procedimientos)
INVALID_DIAGNOSIS_TERMS = [
    'audiometr', 'rayos x', 'rayos-x', 'rx ', 'rx.', 'laboratorio',
    'electrocardiograma', 'ecg', 'ekg', 'examen', 'evaluación',
    'evaluacion', 'control', 'toma de', 'prueba', 'espirometr',
    'optometr', 'visiometr', 'hemograma', 'glicemia', 'colesterol',
    'creatinina', 'parcial de orina', 'coprológico', 'coprologico',
    'ecografía', 'ecografia', 'resonancia', 'tomografía', 'tomografia',
    'radiografía', 'radiografia', 'laboratorios', 'paraclínicos',
    'paraclinicos', 'análisis', 'analisis'
]


def filter_invalid_diagnoses(diagnosticos: list[dict]) -> list[dict]:
    """
    Filtra diagnósticos que en realidad son nombres de exámenes o procedimientos.

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
        if not descripcion:
            continue

        descripcion_lower = descripcion.lower().strip()

        # Verificar si contiene algún término inválido
        is_invalid = any(
            term in descripcion_lower
            for term in INVALID_DIAGNOSIS_TERMS
        )

        if not is_invalid:
            valid_diagnosticos.append(diag)
        else:
            logger.debug(
                f"Diagnóstico filtrado (nombre de examen): '{descripcion}'"
            )

    logger.debug(
        f"Filtrado de diagnósticos: {len(diagnosticos)} → {len(valid_diagnosticos)}"
    )

    return valid_diagnosticos


# Lista de patrones genéricos a filtrar (normalizados sin tildes ni mayúsculas)
GENERIC_RECOMMENDATION_PATTERNS = [
    'pausas activas', 'pausas laborales', 'pausas de descanso',
    'uso de epp', 'uso de elementos de proteccion', 'hacer uso de epp',
    'uso de equipo de proteccion',
    'mantener habitos saludables', 'estilo de vida saludable',
    'realizar ejercicio', 'actividad fisica regular', 'ejercicio regular',
    'alimentacion sana', 'alimentacion saludable', 'dieta balanceada',
    'hidratacion', 'tomar agua', 'consumo de agua',
    'higiene postural', 'buena postura', 'adoptar buena postura',
    'adoptar postura', 'corregir postura',
    'seguridad vial', 'apto para conduccion', 'conduccion segura',
    'llevar estilo de vida', 'mantener vida saludable'
]


def normalize_text_for_comparison(text: str) -> str:
    """
    Normaliza texto para comparación: lowercase, sin tildes, sin símbolos.

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
    return text


def filter_generic_recommendations(recomendaciones: list[dict]) -> list[dict]:
    """
    Filtra recomendaciones genéricas que no aportan valor clínico específico.

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

        # Verificar si contiene algún patrón genérico
        is_generic = any(
            pattern in desc_normalized
            for pattern in GENERIC_RECOMMENDATION_PATTERNS
        )

        if not is_generic:
            filtered.append(rec)
        else:
            logger.debug(f"Recomendación genérica filtrada: '{descripcion}'")

    logger.debug(
        f"Filtrado de recomendaciones: {len(recomendaciones)} → {len(filtered)}"
    )

    return filtered


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
]


def is_pure_negation(desc: str) -> bool:
    """
    Determina si una descripción de antecedente es una negación pura.

    Una negación pura es texto que solo indica ausencia de antecedentes,
    sin mencionar condiciones clínicas específicas.

    Args:
        desc: Descripción del antecedente

    Returns:
        bool: True si es negación pura, False si contiene información clínica
    """
    if not desc:
        return False

    text = normalize_text_for_comparison(desc)

    # Descripciones muy largas suelen incluir más contexto: no son negación pura
    if len(text) > 80:
        return False

    negation_hit = any(term in text for term in NEGATION_TERMS)

    # Si menciona alguna condición concreta, no es solo negación
    clinical_keywords = [
        "hipertension", "hta", "diabetes", "dm", "asma",
        "fractura", "cirugia", "tumor", "cancer", "epilepsia",
        "alergia", "medicamento", "tratamiento", "hospitalizacion"
    ]
    has_clinical = any(k in text for k in clinical_keywords)

    return negation_hit and not has_clinical


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

            # Postprocesamiento: Reclasificar EPP mal ubicado en restricciones
            historia_dict = reclassify_epp_as_recommendations(historia_dict)

            # Postprocesamiento: Consolidar antecedentes con negaciones puras
            if 'antecedentes' in historia_dict and historia_dict['antecedentes']:
                historia_dict['antecedentes'] = consolidate_negation_antecedentes(
                    historia_dict['antecedentes']
                )

            # Agregar metadata
            historia_dict["archivo_origen"] = archivo_origen

            # Validar contra schema Pydantic
            historia = HistoriaClinicaEstructurada.model_validate(historia_dict)

            # Ejecutar validaciones adicionales
            alertas_adicionales = validate_historia_completa(historia)

            # Agregar alertas de validación
            historia.alertas_validacion.extend(alertas_adicionales)

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
