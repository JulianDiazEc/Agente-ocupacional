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

PASO 0: CLASIFICACIÓN DEL DOCUMENTO (CRÍTICO)

Primero, identifica el tipo de documento:

1. "hc_completa" - Historia Clínica Ocupacional COMPLETA:
   - Contiene: anamnesis, examen físico completo, antecedentes, diagnósticos, aptitud laboral
   - Tiene secciones: datos demográficos, signos vitales, revisión por sistemas
   - Es el documento PRINCIPAL de evaluación ocupacional

2. "cmo" - Certificado Médico Ocupacional:
   - Documento de conclusión con aptitud laboral y recomendaciones
   - Puede tener resumen de diagnósticos y restricciones
   - Generalmente más breve que HC completa

3. "examen_especifico" - Examen Aislado (RX, Labs, Optometría, Espirometría, Audiometría, etc.):
   - SOLO contiene resultados de UN examen específico
   - NO tiene anamnesis completa ni examen físico general
   - NO tiene signos vitales generales (PA, FC, FR, temperatura)
   - NO tiene datos demográficos completos
   - Ejemplos: Rayos X tórax, Laboratorios, Optometría, Visiometría, Espirometría, Audiometría

REGLAS SEGÚN TIPO DE DOCUMENTO:

SI tipo_documento_fuente = "examen_especifico":
  ✅ EXTRAER SOLO:
     - tipo_documento_fuente: "examen_especifico"
     - tipo_emo: null (no es obligatorio en exámenes aislados)
     - datos_empleado: solo documento/nombre si aparece explícitamente
     - signos_vitales: null (no se esperan en exámenes específicos)
     - examenes: [el examen específico con todos sus resultados y valores]
     - diagnosticos: solo si el examen incluye interpretación diagnóstica

  ❌ NO GENERAR ALERTAS POR:
     - Falta de signos vitales
     - Falta de datos demográficos completos (edad, sexo, EPS, ARL)
     - Falta de tipo_emo explícito
     - Falta de aptitud laboral

SI tipo_documento_fuente = "hc_completa" O "cmo":
  ✅ EXTRAER TODO según reglas normales
  ✅ GENERAR alertas por datos faltantes

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

   ⚠️ REGLA ANTI-FALSOS POSITIVOS:
   a) diagnosticos.tipo - SOLO cuando EXPLÍCITO:
      ✅ Llenar SOLO si el documento dice textualmente:
         - "diagnóstico principal", "Dx principal"
         - "diagnóstico secundario", "Dx secundario"
         - "hallazgo"
      ❌ NO asumir por posición en lista o contexto
      ❌ Si NO está explícito: dejar en null

   b) diagnosticos.descripcion - DEBE ser diagnóstico REAL:
      ✅ Extraer diagnósticos médicos reales:
         - "Hipertensión arterial"
         - "Diabetes mellitus tipo 2"
         - "Hipoacusia neurosensorial bilateral"
      ❌ NO extraer nombres de exámenes/procedimientos:
         - "Audiometría" → NO es diagnóstico
         - "Rayos X de tórax" → NO es diagnóstico
         - "Laboratorio clínico" → NO es diagnóstico
         - "Electrocardiograma" → NO es diagnóstico
         - "Evaluación", "Control" → NO son diagnósticos
      REGLA: Si dice el nombre de un examen, NO es un diagnóstico

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

      ⚠️ REGLA ANTI-RUIDO DE NORMALIDAD:
      - Si TODO el examen físico es NORMAL (ej: "cabeza normocéfala", "cuello simétrico sin masas", etc.):
        → Resumir como: "examen físico sin hallazgos relevantes" o "sin hallazgos patológicos"
      - Si hay hallazgos POSITIVOS/ANORMALES:
        → Reportar SOLO los hallazgos positivos/anormales
        → OMITIR listados largos de normalidad
      - NO listar cada sistema normal individualmente si todos son normales
      - Priorizar: RESUMEN + HALLAZGOS POSITIVOS solamente

   b) ANTECEDENTES:
      ⚠️ REGLA ANTI-FALSOS POSITIVOS - NEGACIÓN GLOBAL:
      - Si el documento dice: "NIEGA antecedentes", "sin antecedentes personales/familiares",
        "no refiere antecedentes", o similar:
        → NO crear entradas individuales por categoría con texto "NIEGA" o "sin antecedentes"
        → Crear UNA SOLA entrada:
          * tipo: "general" (o el tipo más apropiado si especifica)
          * descripcion: "sin antecedentes relevantes" o "niega antecedentes personales y familiares"
      - Si menciona antecedentes ESPECÍFICOS: extraer normalmente con su categoría

   c) LABORATORIOS CLÍNICOS - TODOS LOS VALORES:
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

7. DATOS DEL EMPLEADO - REGLAS ANTI-FALSOS POSITIVOS:

   a) TIPO DE DOCUMENTO:
      ⚠️ REGLA CRÍTICA ANTI-FALSOS POSITIVOS:
      ✅ Extraer SOLO si aparece etiqueta EXPLÍCITA:
         - "Tipo de documento: CC" → tipo_documento: "CC"
         - "Documento: CC 12345678" → tipo_documento: "CC"
         - "Cédula de Ciudadanía N°..." → tipo_documento: "CC"
         - "C.C:" o "CC:" seguido de número → tipo_documento: "CC"
         - "TI:" o "Tarjeta de Identidad:" → tipo_documento: "TI"
         - "CE:" o "Cédula de Extranjería:" → tipo_documento: "CE"
         - "Pasaporte:" → tipo_documento: "PEP" o "PPT"

      ❌ NO EXTRAER en estos casos:
         - "CC" aparece dentro de palabras: "dire**cc**ión", "protec**cc**ión", "reac**cc**ión"
         - "CC" aparece en contexto NO relacionado con identificación
         - Ejemplo: "dirección CC 123" → NO extraer "CC" como tipo_documento

      REGLA ESTRICTA:
      - Usar búsqueda de PALABRA COMPLETA (word boundary)
      - El tipo de documento debe estar asociado a sección de identificación/datos personales
      - NO inferir solo por formato de número (ej: un número de 8 dígitos NO implica que sea CC)
      - Si hay CUALQUIER duda: usar null

   b) CARGO:
      ✅ EXTRAER cargos específicos y útiles:
         - "Operario de producción"
         - "Contador"
         - "Auxiliar de enfermería"
         - "Conductor"
         - "Soldador"

      ❌ NO EXTRAER valores genéricos o ambiguos:
         - "Empleado" → Demasiado genérico, usa null
         - "Trabajador" → Demasiado genérico, usa null
         - "Ocupación: empleado" → NO extraer, usa null
         - "Personal" → Demasiado genérico, usa null

      REGLA: El cargo debe ser específico y describir la función/rol real.
      Si solo dice "empleado" o "trabajador", mejor usa null.

   c) OTROS CAMPOS DEMOGRÁFICOS:
      - Edad: Solo si es numérica y razonable (16-100)
      - Sexo: Solo M, F, O (no "masculino", "femenino" - convertir a letra)
      - Documento: Extraer el número completo sin puntos ni espacios

9. DATOS FALTANTES:
   - Si un campo no está en la HC, usa null
   - NO inventes valores médicos
   - Si algo es ambiguo, extráelo y marca confianza baja + alerta

10. NIVEL DE CONFIANZA:
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


def get_extraction_prompt_cached(
    texto_extraido: str,
    schema_json: Dict[str, Any] | None = None,
    context: Dict[str, str] | None = None
) -> tuple[list[dict], str]:
    """
    Genera el prompt para extracción CON SOPORTE DE CACHING.

    Separa el prompt en bloques cacheables (instrucciones + schema)
    y contenido variable (texto del PDF).

    Args:
        texto_extraido: Texto extraído del PDF por Azure
        schema_json: JSON Schema del modelo (opcional, se genera automáticamente)
        context: Contexto adicional (nombre archivo, empresa, etc.)

    Returns:
        tuple[list[dict], str]: (system_blocks_con_cache, user_message)
    """

    # Generar schema si no se proporciona
    if schema_json is None:
        schema_json = HistoriaClinicaEstructurada.model_json_schema()

    # Context adicional
    context_str = ""
    if context:
        context_items = [f"- {k}: {v}" for k, v in context.items()]
        context_str = "\n".join(context_items)

    # BLOQUE 1: Instrucciones base (CACHEABLE)
    instrucciones_base = f"""Eres un experto médico ocupacional especializado en la evaluación de Exámenes Médicos Ocupacionales (EMO) en Colombia. Tu tarea es analizar historias clínicas de EMO y extraer TODA la información estructurada con precisión clínica, sin filtrar ni omitir hallazgos.

PASO 0: CLASIFICACIÓN DEL DOCUMENTO (CRÍTICO)

Primero, identifica el tipo de documento:

1. "hc_completa" - Historia Clínica Ocupacional COMPLETA:
   - Contiene: anamnesis, examen físico completo, antecedentes, diagnósticos, aptitud laboral
   - Tiene secciones: datos demográficos, signos vitales, revisión por sistemas
   - Es el documento PRINCIPAL de evaluación ocupacional

2. "cmo" - Certificado Médico Ocupacional:
   - Documento de conclusión con aptitud laboral y recomendaciones
   - Puede tener resumen de diagnósticos y restricciones
   - Generalmente más breve que HC completa

3. "examen_especifico" - Examen Aislado (RX, Labs, Optometría, Espirometría, Audiometría, etc.):
   - SOLO contiene resultados de UN examen específico
   - NO tiene anamnesis completa ni examen físico general
   - NO tiene signos vitales generales (PA, FC, FR, temperatura)
   - NO tiene datos demográficos completos
   - Ejemplos: Rayos X tórax, Laboratorios, Optometría, Visiometría, Espirometría, Audiometría

REGLAS SEGÚN TIPO DE DOCUMENTO:

SI tipo_documento_fuente = "examen_especifico":
  ✅ EXTRAER SOLO:
     - tipo_documento_fuente: "examen_especifico"
     - tipo_emo: null (no es obligatorio en exámenes aislados)
     - datos_empleado: solo documento/nombre si aparece explícitamente
     - signos_vitales: null (no se esperan en exámenes específicos)
     - examenes: [el examen específico con todos sus resultados y valores]
     - diagnosticos: solo si el examen incluye interpretación diagnóstica

  ❌ NO GENERAR ALERTAS POR:
     - Falta de signos vitales
     - Falta de datos demográficos completos (edad, sexo, EPS, ARL)
     - Falta de tipo_emo explícito
     - Falta de aptitud laboral

SI tipo_documento_fuente = "hc_completa" O "cmo":
  ✅ EXTRAER TODO según reglas normales
  ✅ GENERAR alertas por datos faltantes

CONTEXTO:
Los EMO son evaluaciones obligatorias según la Resolución 2346 de 2007 en Colombia. Sirven para determinar la aptitud laboral, detectar condiciones de salud relacionadas con el trabajo, y establecer recomendaciones preventivas.

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

   ⚠️ REGLA ANTI-FALSOS POSITIVOS:
   a) diagnosticos.tipo - SOLO cuando EXPLÍCITO:
      ✅ Llenar SOLO si el documento dice textualmente:
         - "diagnóstico principal", "Dx principal"
         - "diagnóstico secundario", "Dx secundario"
         - "hallazgo"
      ❌ NO asumir por posición en lista o contexto
      ❌ Si NO está explícito: dejar en null

   b) diagnosticos.descripcion - DEBE ser diagnóstico REAL:
      ✅ Extraer diagnósticos médicos reales:
         - "Hipertensión arterial"
         - "Diabetes mellitus tipo 2"
         - "Hipoacusia neurosensorial bilateral"
      ❌ NO extraer nombres de exámenes/procedimientos:
         - "Audiometría" → NO es diagnóstico
         - "Rayos X de tórax" → NO es diagnóstico
         - "Laboratorio clínico" → NO es diagnóstico
         - "Electrocardiograma" → NO es diagnóstico
         - "Evaluación", "Control" → NO son diagnósticos
      REGLA: Si dice el nombre de un examen, NO es un diagnóstico

2. FECHAS:
   - Formato obligatorio: YYYY-MM-DD (ISO 8601)
   - Fecha del EMO, fecha de exámenes paraclínicos, fechas de seguimiento
   - Si solo encuentras mes/año, usa día 01 (ej: "marzo 2024" → "2024-03-01")
   - Si la fecha es ambigua o ilegible, extrae lo que puedas y marca confianza baja

3. HALLAZGOS CLÍNICOS - EXTRAER TODO SIN EXCEPCIÓN:
   REGLA DE ORO: Eres un extractor de datos, NO un filtrador clínico.
   Tu trabajo es documentar TODO lo que encuentres, incluso si parece menor o irrelevante.
   El médico humano decidirá qué es importante.

4. APTITUD LABORAL:
   ⚠️ REGLA CRÍTICA - SOLO CONCEPTO EXPLÍCITO:
   - Extrae EXACTAMENTE lo que dice el certificado/concepto médico ocupacional
   - NO interpretar ni modificar basándose en:
     * Presencia de recomendaciones
     * Hallazgos en exámenes
     * Diagnósticos encontrados

   Valores posibles:
   - "apto" / "apto_sin_restricciones" → Si dice "APTO" sin restricciones
   - "apto_con_recomendaciones" → Si dice "APTO CON RECOMENDACIONES"
   - "apto_con_restricciones" → Si dice "APTO CON RESTRICCIONES"
   - "no_apto_temporal" → Si dice "NO APTO TEMPORAL"
   - "no_apto_definitivo" → Si dice "NO APTO DEFINITIVO"
   - "pendiente" → Si dice "PENDIENTE"

   IMPORTANTE:
   - Si dice "APTO", es "apto" (aunque haya recomendaciones de seguimiento)
   - Si NO hay concepto explícito de aptitud: usar null
   - NO cambiar aptitud solo porque hay hallazgos o recomendaciones

5. RECOMENDACIONES - SOLO LAS ESPECÍFICAS:
   ✅ EXTRAER:
   - Remisiones a especialistas
   - Exámenes complementarios específicos
   - Inclusión en programas SVE
   - Tratamientos específicos

   ❌ NO EXTRAER (genéricas):
   - "Pausas activas"
   - "Uso de EPP"
   - "Mantener hábitos saludables"

   ⚠️ CAMPOS A LLENAR:
   - tipo: (remision_especialista, examen_complementario, inclusion_sve, tratamiento, restriccion_laboral, ajuste_ergonomico, seguimiento)
   - descripcion: texto específico de la recomendación
   - vigencia_meses: solo si se menciona explícitamente
   - requiere_seguimiento: true/false

   ⚠️ RESTRICCIÓN LABORAL vs RECOMENDACIÓN GENERAL:
   - Marcar tipo como "restriccion_laboral" SOLO cuando el documento diga EXPLÍCITAMENTE:
     * "restricción para..."
     * "no apto para..."
     * "limitación laboral para..."
     * "debe evitar..." (en contexto de limitación)
   - Recomendaciones de seguimiento médico/controles: tipo "seguimiento", NO "restriccion_laboral"
   - Remisiones a especialistas: tipo "remision_especialista", NO "restriccion_laboral"

6. RESTRICCIONES LABORALES (campo restricciones_especificas):

   ⚠️ DISTINCIÓN CRÍTICA - Restricción vs Recomendación:

   restricciones_especificas es un campo de TEXTO LIBRE que contiene SOLO:
   - Limitaciones o PROHIBICIONES de ACTIVIDAD LABORAL específicas

   ✅ SÍ va en restricciones_especificas:
      - "No levantar cargas mayores a 15kg"
      - "No trabajar en alturas superiores a 1.5m"
      - "Evitar exposición a solventes orgánicos"
      - "No conducir vehículos"
      - "No trabajar en turno nocturno"
      - "Evitar movimientos repetitivos de flexo-extensión de muñeca"
      - "No permanecer de pie por más de 4 horas continuas"

   ❌ NO va en restricciones_especificas (van en recomendaciones):
      - "Uso de lentes de corrección" → Es recomendación de EPP
      - "Uso de protector auditivo" → Es recomendación de EPP
      - "Uso de guantes" → Es recomendación de EPP
      - "Control médico en 6 meses" → Es recomendación de seguimiento
      - "Remisión a oftalmología" → Es recomendación de remisión
      - "Pausas activas" → Es recomendación general
      - "Ajuste de silla ergonómica" → Es recomendación de ajuste ergonómico

   REGLA DE ORO:
   - Si dice "NO [verbo]" o "EVITAR [actividad]" → restricciones_especificas
   - Si dice "USO DE [EPP]" o "CONTROL [médico]" → recomendaciones
   - Si NO hay restricciones explícitas de actividad → dejar campo vacío (null)

7. VALIDACIÓN Y ALERTAS:
   Genera alertas cuando detectes:
   a) INCONSISTENCIAS DIAGNÓSTICAS: Diagnóstico sin soporte en exámenes
   b) DATOS FALTANTES CRÍTICOS: Diagnóstico sin código CIE-10, aptitud no definida
   c) VALORES CRÍTICOS: PA ≥180/110, Glicemia ≥200, IMC <16 o >40
   d) FORMATO INCORRECTO: Código CIE-10 erróneo, fechas no ISO

8. DATOS DEL EMPLEADO - REGLAS ANTI-FALSOS POSITIVOS:

   a) TIPO DE DOCUMENTO:
      ⚠️ REGLA CRÍTICA ANTI-FALSOS POSITIVOS:
      ✅ Extraer SOLO si aparece etiqueta EXPLÍCITA:
         - "Tipo de documento: CC" → tipo_documento: "CC"
         - "Documento: CC 12345678" → tipo_documento: "CC"
         - "Cédula de Ciudadanía N°..." → tipo_documento: "CC"
         - "C.C:" o "CC:" seguido de número → tipo_documento: "CC"
         - "TI:" o "Tarjeta de Identidad:" → tipo_documento: "TI"
         - "CE:" o "Cédula de Extranjería:" → tipo_documento: "CE"
         - "Pasaporte:" → tipo_documento: "PEP" o "PPT"

      ❌ NO EXTRAER en estos casos:
         - "CC" aparece dentro de palabras: "dire**cc**ión", "protec**cc**ión", "reac**cc**ión"
         - "CC" aparece en contexto NO relacionado con identificación
         - Ejemplo: "dirección CC 123" → NO extraer "CC" como tipo_documento

      REGLA ESTRICTA:
      - Usar búsqueda de PALABRA COMPLETA (word boundary)
      - El tipo de documento debe estar asociado a sección de identificación/datos personales
      - NO inferir solo por formato de número (ej: un número de 8 dígitos NO implica que sea CC)
      - Si hay CUALQUIER duda: usar null

   b) CARGO:
      ✅ EXTRAER cargos específicos y útiles:
         - "Operario de producción"
         - "Contador"
         - "Auxiliar de enfermería"
         - "Conductor"
         - "Soldador"

      ❌ NO EXTRAER valores genéricos o ambiguos:
         - "Empleado" → Demasiado genérico, usa null
         - "Trabajador" → Demasiado genérico, usa null
         - "Ocupación: empleado" → NO extraer, usa null
         - "Personal" → Demasiado genérico, usa null

      REGLA: El cargo debe ser específico y describir la función/rol real.
      Si solo dice "empleado" o "trabajador", mejor usa null.

   c) OTROS CAMPOS DEMOGRÁFICOS:
      - Edad: Solo si es numérica y razonable (16-100)
      - Sexo: Solo M, F, O (no "masculino", "femenino" - convertir a letra)
      - Documento: Extraer el número completo sin puntos ni espacios

9. DATOS FALTANTES:
   - Si un campo no está en la HC, usa null
   - NO inventes valores médicos
   - Si algo es ambiguo, extráelo y marca confianza baja + alerta

10. NIVEL DE CONFIANZA:
   - 1.0: Dato explícito y claro
   - 0.9: Dato explícito pero formato no estándar
   - 0.7: Dato con jerga médica ambigua
   - 0.5: Dato inferido de contexto
   - 0.3: Dato parcialmente legible"""

    # BLOQUE 2: JSON Schema (CACHEABLE)
    schema_block = f"""SCHEMA JSON A SEGUIR:
{json.dumps(schema_json, indent=2, ensure_ascii=False)}

INSTRUCCIONES FINALES:
1. Retorna ÚNICAMENTE un objeto JSON válido que cumpla el schema
2. NO agregues texto explicativo fuera del JSON
3. NO uses markdown code blocks (```json)
4. Usa null para campos faltantes
5. Genera alertas para todo lo que requiera revisión médica
6. Calcula confianza global como promedio de confianzas individuales"""

    # System blocks con cache control
    system_blocks = [
        {
            "type": "text",
            "text": instrucciones_base,
            "cache_control": {"type": "ephemeral"}  # Cache por 5 minutos
        },
        {
            "type": "text",
            "text": schema_block,
            "cache_control": {"type": "ephemeral"}  # Cache por 5 minutos
        }
    ]

    # User message (contenido variable, NO se cachea)
    context_header = ""
    if context_str:
        context_header = f"""INFORMACIÓN ADICIONAL DEL DOCUMENTO:
{context_str}

"""

    user_message = f"""{context_header}TEXTO EXTRAÍDO DE LA HISTORIA CLÍNICA:
==================================================
{texto_extraido}
==================================================

RETORNA EL JSON AHORA:"""

    return system_blocks, user_message


__all__ = [
    "get_extraction_prompt",
    "get_extraction_prompt_cached",
    "get_validation_prompt",
    "get_correction_prompt"
]
