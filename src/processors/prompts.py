"""
Prompts optimizados para extracción de historias clínicas con Claude API.
"""

import json
from typing import Any, Dict

from src.config.schemas import HistoriaClinicaEstructurada


def get_extraction_prompt(
    texto_extraido: str,
    schema_json: Dict[str, Any] | None = None,
    context: Dict[str, str] | None = None
) -> str:
    """
    Genera el prompt maestro para extracción de historia clínica.

    Args:
        texto_extraido: Texto extraído del PDF por Azure
        schema_json: JSON Schema del modelo (opcional, se genera automáticamente)
        context: Contexto adicional (nombre archivo, empresa, etc.)

    Returns:
        str: Prompt completo para Claude API
    """

    # Generar schema si no se proporciona
    if schema_json is None:
        schema_json = HistoriaClinicaEstructurada.model_json_schema()

    # Context adicional
    context_str = ""
    if context:
        context_items = [f"- {k}: {v}" for k, v in context.items()]
        context_str = "\n".join(context_items)

    prompt = f"""Eres un experto médico ocupacional especializado en la evaluación de Exámenes Médicos Ocupacionales (EMO) en Colombia. Tu tarea es analizar historias clínicas de EMO y extraer TODA la información estructurada con precisión clínica, sin filtrar ni omitir hallazgos.

CONTEXTO:
Los EMO son evaluaciones obligatorias según la Resolución 2346 de 2007 en Colombia. Sirven para determinar la aptitud laboral, detectar condiciones de salud relacionadas con el trabajo, y establecer recomendaciones preventivas.

{f"INFORMACIÓN ADICIONAL DEL DOCUMENTO:" if context_str else ""}
{context_str}

TIPOS DE EMO QUE PUEDES ENCONTRAR:
- Preingreso: Evaluación antes de vincular al empleado
- Periódico: Seguimiento de salud según exposición ocupacional
- Post-incapacidad: Evaluación tras ausencia médica prolongada
- Cambio de ocupación: Al cambiar de puesto/exposición
- Retiro/Egreso: Al finalizar vínculo laboral

REGLAS CRÍTICAS DE EXTRACCIÓN:

1. DIAGNÓSTICOS (CIE-10):
   - Formato EXACTO: Letra + 2 dígitos + punto + 1 dígito (ej: M54.5, J30.1, H52.0)
   - Extrae TODOS los diagnósticos mencionados, sin excepción
   - Diferencia diagnósticos principales vs hallazgos incidentales
   - Identifica si son preexistentes o relacionados con el trabajo
   - Si el formato CIE-10 es incorrecto o falta, extrae de todas formas y genera alerta

2. FECHAS:
   - Formato obligatorio: YYYY-MM-DD (ISO 8601)
   - Fecha del EMO, fecha de exámenes paraclínicos, fechas de seguimiento
   - Si solo encuentras mes/año, usa día 01 (ej: "marzo 2024" → "2024-03-01")
   - Si la fecha es ambigua o ilegible, extrae lo que puedas y marca confianza baja

3. HALLAZGOS CLÍNICOS - EXTRAER TODO SIN EXCEPCIÓN:

   REGLA DE ORO: Eres un extractor de datos, NO un filtrador clínico.
   Tu trabajo es documentar TODO lo que encuentres, incluso si parece menor o irrelevante.
   El médico humano decidirá qué es importante.

   a) EXAMEN FÍSICO:
      - Signos vitales: PA, FC, FR, Temperatura, Saturación O2, IMC
      - Hallazgos en TODOS los sistemas explorados

   b) LABORATORIOS CLÍNICOS - TODOS LOS VALORES:
      - Hemograma, glucemia, perfil lipídico, función renal/hepática, etc.
      - FORMATO: "Nombre: Valor (Rango: X-Y) [Estado: normal/alto/bajo]"

   c) IMAGENOLOGÍA - TODOS LOS ESTUDIOS:
      - Rayos X, ecografías, TAC, resonancias (hallazgos completos)

   d) PRUEBAS FUNCIONALES - TODOS LOS RESULTADOS:
      - Audiometría: frecuencias, umbrales en dB, tipo de pérdida
      - Espirometría: FEV1, FVC, patrón, % predicho
      - Visiometría: agudeza visual con/sin corrección
      - ECG: ritmo, FC, intervalos, interpretación

4. APTITUD LABORAL:
   Busca EXPLÍCITAMENTE el concepto de aptitud. Valores posibles:
   - "apto" / "apto_sin_restricciones"
   - "apto_con_recomendaciones"
   - "apto_con_restricciones"
   - "no_apto_temporal"
   - "no_apto_definitivo"
   - "pendiente"

   Si no está explícito, usa null y genera alerta.

5. RECOMENDACIONES - SOLO LAS ESPECÍFICAS:

   ✅ EXTRAER:
   - Remisiones a especialistas
   - Exámenes complementarios específicos
   - Inclusión en programas SVE específicos
   - Restricciones laborales con valores (ej: "No cargar >15kg")

   ❌ NO EXTRAER (genéricas):
   - "Pausas activas"
   - "Uso de EPP"
   - "Mantener hábitos saludables"
   - Cualquier recomendación universal

6. VALIDACIÓN Y ALERTAS:

   Genera alertas cuando detectes:

   a) INCONSISTENCIAS DIAGNÓSTICAS:
      - Diagnóstico sin soporte en exámenes
      - Hallazgo sin diagnóstico correspondiente

   b) DATOS FALTANTES CRÍTICOS:
      - Diagnóstico sin código CIE-10
      - Aptitud laboral no definida

   c) VALORES CRÍTICOS:
      - PA ≥180/110
      - Glicemia ≥200 mg/dL
      - IMC <16 o >40

   d) FORMATO INCORRECTO:
      - Código CIE-10 con formato erróneo
      - Fechas en formato no ISO

7. DATOS FALTANTES:
   - Si un campo no está en la HC, usa null
   - NO inventes valores médicos
   - Si algo es ambiguo, extráelo y marca confianza baja + alerta

8. NIVEL DE CONFIANZA:
   - 1.0: Dato explícito y claro
   - 0.9: Dato explícito pero formato no estándar
   - 0.7: Dato con jerga médica ambigua
   - 0.5: Dato inferido de contexto
   - 0.3: Dato parcialmente legible

TEXTO EXTRAÍDO DE LA HISTORIA CLÍNICA:
==================================================
{texto_extraido}
==================================================

SCHEMA JSON A SEGUIR:
{json.dumps(schema_json, indent=2, ensure_ascii=False)}

INSTRUCCIONES FINALES:
1. Retorna ÚNICAMENTE un objeto JSON válido que cumpla el schema
2. NO agregues texto explicativo fuera del JSON
3. NO uses markdown code blocks (```json)
4. Usa null para campos faltantes
5. Genera alertas para todo lo que requiera revisión médica
6. Calcula confianza global como promedio de confianzas individuales

RETORNA EL JSON AHORA:"""

    return prompt


def get_validation_prompt(
    historia_json: Dict[str, Any],
    ground_truth_json: Dict[str, Any]
) -> str:
    """
    Genera prompt para validación de extracción contra ground truth.

    Args:
        historia_json: Historia clínica extraída
        ground_truth_json: Ground truth etiquetado manualmente

    Returns:
        str: Prompt para validación
    """
    return f"""Eres un evaluador experto de sistemas de extracción de información médica.

Compara la siguiente historia clínica extraída automáticamente contra el ground truth etiquetado manualmente.

HISTORIA EXTRAÍDA:
{json.dumps(historia_json, indent=2, ensure_ascii=False)}

GROUND TRUTH:
{json.dumps(ground_truth_json, indent=2, ensure_ascii=False)}

Evalúa:
1. Precisión de diagnósticos (CIE-10 correctos)
2. Completitud de extracción (campos faltantes)
3. Exactitud de fechas
4. Correctitud de aptitud laboral
5. Calidad de alertas generadas

Retorna un JSON con:
{{
    "precision_diagnosticos": 0.95,
    "recall_diagnosticos": 0.90,
    "precision_examenes": 0.88,
    "recall_examenes": 0.85,
    "exactitud_fechas": 0.92,
    "exactitud_aptitud": 1.0,
    "score_global": 0.90,
    "errores_criticos": [],
    "errores_menores": [],
    "recomendaciones": []
}}"""


def get_correction_prompt(
    historia_json: Dict[str, Any],
    errors: list[str]
) -> str:
    """
    Genera prompt para corrección de errores detectados.

    Args:
        historia_json: Historia clínica con errores
        errors: Lista de errores detectados

    Returns:
        str: Prompt para corrección
    """
    errors_str = "\n".join(f"- {error}" for error in errors)

    return f"""Corrige los siguientes errores en la historia clínica estructurada:

ERRORES DETECTADOS:
{errors_str}

HISTORIA CLÍNICA ACTUAL:
{json.dumps(historia_json, indent=2, ensure_ascii=False)}

Retorna la historia clínica corregida en formato JSON válido.
Mantén todos los campos que no tienen errores.
Solo modifica lo necesario para corregir los errores listados."""


__all__ = [
    "get_extraction_prompt",
    "get_validation_prompt",
    "get_correction_prompt"
]
