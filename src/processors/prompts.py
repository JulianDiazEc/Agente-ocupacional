"""
Prompts optimizados para extracción de historias clínicas con Claude API.
Consolidado en una función con cache por defecto.
"""

import json
from typing import Any, Dict, Union, Tuple, List

from src.config.schemas import HistoriaClinicaEstructurada


def get_simple_diagnosis_prompt(texto_extraido: str) -> str:
    """
    Prompt ultra-simple específico para extracción de diagnósticos.
    Soluciona el problema de R63.5 y otros diagnósticos perdidos.
    """
    return f"""Encuentra TODOS los códigos CIE-10 en este texto médico.
BUSCA especialmente R63.5 (aumento anormal de peso).

Códigos CIE-10 tienen formato: LETRA + 2 números + punto + 1 número
Ejemplos: R63.5, H52.2, E11.9, I10

TEXTO:
{texto_extraido[:3000]}

Responde SOLO este formato JSON:
{{
    "diagnosticos": [
        {{"codigo_cie10": "R63.5", "descripcion": "AUMENTO ANORMAL DE PESO", "tipo": "principal", "relacionado_trabajo": false, "confianza": 1.0}},
        {{"codigo_cie10": "E11.9", "descripcion": "DIABETES MELLITUS TIPO 2", "tipo": "secundario", "relacionado_trabajo": false, "confianza": 1.0}}
    ]
}}"""


def _get_core_extraction_rules() -> str:
    """
    Reglas médicas centralizadas - mantiene todos los aprendizajes críticos
    """
    return """Eres un experto médico ocupacional especializado en EMO en Colombia. Extrae TODA la información estructurada con precisión clínica.

PASO 0: CLASIFICACIÓN DEL DOCUMENTO (CRÍTICO)

1. "hc_completa" - Historia Clínica Ocupacional COMPLETA (anamnesis, examen físico, diagnósticos, aptitud)
2. "cmo" - Certificado Médico Ocupacional (conclusión con aptitud y restricciones)
3. "examen_especifico" - Examen Aislado (RX, Labs, Audiometría, etc. - SOLO resultados específicos)

REGLAS SEGÚN TIPO:
- examen_especifico: NO generar alertas por falta de signos vitales, datos demográficos o aptitud
- hc_completa/cmo: Extraer todo según reglas normales

REGLAS CRÍTICAS:

0. INTERPRETACIÓN DE TABLAS/CHECKBOXES:
   Patrón común en PDFs:
   ```
   1. SATISFACTORIO
   2. NO SATISFACTORIO  
   3. CON RESTRICCIONES
   X
   ```
   ✅ CORRECTO: X marca la PRIMERA opción (columna 2, fila 1)
   ❌ ERROR: NO es la última opción por aparecer al final

1. DIAGNÓSTICOS (CIE-10):
   - Formato: Letra + 2 dígitos + punto + 1 dígito (M54.5, R63.5, J30.1, H52.0)
   - Extrae TODOS sin excepción, especialmente códigos R (síntomas/signos muy comunes en EMOs)
   - Ejemplos críticos: R63.5 Aumento anormal peso, R06.0 Disnea, R50.9 Fiebre
   
   ANTI-FALSOS POSITIVOS:
   - tipo: Solo si dice explícito "diagnóstico principal/secundario/hallazgo" 
   - descripcion: Solo diagnósticos reales, NO nombres de exámenes ("Audiometría" NO es diagnóstico)

2. APTITUD LABORAL - SOLO CONCEPTO EXPLÍCITO:
   - Extrae EXACTAMENTE lo que dice el documento
   - NO interpretes por hallazgos/recomendaciones
   - Valores: "apto", "apto_con_restricciones", "no_apto_temporal", etc.
   - Si no explícito: null

3. RECOMENDACIONES:
   ❌ NO EXTRAER NINGUNA RECOMENDACIÓN
   - Ignora secciones: "Recomendaciones", "Conducta", "Remisiones", "Seguimiento"
   - Este análisis lo realiza motor ocupacional posterior

4. CHECKBOXES - EVIDENCIA CLARA:
   ✅ Marcas válidas: X, x, ✓, ☑
   ❌ NO son marcas: ', `, ., -, |
   
   Ejemplos OCR:
   ✅ "X USO EPP" → marcado
   ❌ "' REASIGNACION" → apóstrofe = ruido OCR, NO marcado
   
   REGLA: Solo extraer si hay checkbox marcado Y confirmación textual narrativa

5. DATOS EMPLEADO - ANTI-FALSOS POSITIVOS:
   - tipo_documento: Solo con etiqueta explícita "CC:", "TI:", etc.
   - cargo: Solo específicos (NO "empleado"/"trabajador" genéricos)
   - Documento: número completo sin puntos/espacios

6. HALLAZGOS CLÍNICOS:
   REGLA DE ORO: Extractor de datos, NO filtrador clínico.
   
   - Antecedentes: Si dice "NIEGA antecedentes" → UNA entrada: "sin antecedentes relevantes"
   - Examen físico: Si todo normal → resumir, NO listar cada sistema
   - Laboratorios: Todos los valores con formato "Nombre: Valor (Rango) [Estado]"

7. FORMATOS:
   - Fechas: YYYY-MM-DD obligatorio
   - Confianza: 1.0=explícito, 0.9=formato no estándar, 0.7=ambiguo, 0.5=inferido, 0.3=parcial
   - Datos faltantes: null (NO inventar valores)"""


def get_extraction_prompt(
    texto_extraido: str,
    schema_json: Dict[str, Any] | None = None,
    context: Dict[str, str] | None = None,
    use_cache: bool = True  # 🔥 CACHE POR DEFECTO
) -> Union[str, Tuple[List[Dict], str]]:
    """
    Función unificada para extracción con cache por defecto.
    Mantiene todos los aprendizajes del prompt original.

    Args:
        texto_extraido: Texto extraído del PDF por Azure
        schema_json: JSON Schema del modelo (opcional)
        context: Contexto adicional (empresa, archivo, etc.)
        use_cache: Si True (defecto), usa cache. Si False, formato simple.

    Returns:
        Union[str, Tuple[List[Dict], str]]: Formato cache o prompt simple
    """
    
    # Generar schema si no se proporciona
    if schema_json is None:
        schema_json = HistoriaClinicaEstructurada.model_json_schema()

    # Preparar componentes
    rules = _get_core_extraction_rules()
    schema_str = json.dumps(schema_json, indent=2, ensure_ascii=False)
    
    # Context adicional
    context_str = ""
    if context:
        context_items = [f"- {k}: {v}" for k, v in context.items()]
        context_str = f"INFORMACIÓN ADICIONAL:\n" + "\n".join(context_items) + "\n\n"

    # Instrucciones finales (SIN ALERTAS EN RESUMEN MÉDICO)
    final_instructions = """INSTRUCCIONES FINALES:
1. Retorna ÚNICAMENTE JSON válido que cumpla el schema
2. NO agregues texto explicativo fuera del JSON
3. NO uses markdown code blocks
4. Usa null para campos faltantes
5. NO generes alertas en el campo resumen_medico
6. Calcula confianza global como promedio de confianzas individuales"""

    if use_cache:
        # 🚀 FORMATO CON CACHE (POR DEFECTO)
        system_blocks = [
            {
                "type": "text",
                "text": rules,
                "cache_control": {"type": "ephemeral"}
            },
            {
                "type": "text",
                "text": f"SCHEMA JSON A SEGUIR:\n{schema_str}\n\n{final_instructions}",
                "cache_control": {"type": "ephemeral"}
            }
        ]
        
        user_message = f"""{context_str}TEXTO EXTRAÍDO DE LA HISTORIA CLÍNICA:
==================================================
{texto_extraido}
==================================================

RETORNA EL JSON AHORA:"""
        
        return system_blocks, user_message
    
    else:
        # 📝 FORMATO SIMPLE (SOLO SI SE SOLICITA EXPLÍCITAMENTE)
        return f"""{rules}

{context_str}TEXTO EXTRAÍDO DE LA HISTORIA CLÍNICA:
==================================================
{texto_extraido}
==================================================

SCHEMA JSON A SEGUIR:
{schema_str}

{final_instructions}

RETORNA EL JSON AHORA:"""


# Mantener compatibilidad con código existente
def get_extraction_prompt_cached(
    texto_extraido: str,
    schema_json: Dict[str, Any] | None = None,
    context: Dict[str, str] | None = None
) -> Tuple[List[Dict], str]:
    """
    Wrapper para mantener compatibilidad con código existente.
    Ahora simplemente llama a la función principal (que ya usa cache por defecto).
    """
    result = get_extraction_prompt(
        texto_extraido=texto_extraido,
        schema_json=schema_json,
        context=context,
        use_cache=True  # Forzar cache para mantener compatibilidad
    )
    return result  # type: ignore


def get_validation_prompt(
    historia_json: Dict[str, Any],
    ground_truth_json: Dict[str, Any]
) -> str:
    """Prompt para validación contra ground truth."""
    return f"""Evalúa la extracción médica comparando con ground truth:

HISTORIA EXTRAÍDA:
{json.dumps(historia_json, indent=2, ensure_ascii=False)}

GROUND TRUTH:
{json.dumps(ground_truth_json, indent=2, ensure_ascii=False)}

Retorna JSON con métricas de precisión y recall por categoría."""


def get_correction_prompt(
    historia_json: Dict[str, Any],
    errors: List[str]
) -> str:
    """Prompt para corrección de errores detectados."""
    errors_str = "\n".join(f"- {error}" for error in errors)

    return f"""Corrige los siguientes errores en la historia clínica:

ERRORES DETECTADOS:
{errors_str}

HISTORIA CLÍNICA ACTUAL:
{json.dumps(historia_json, indent=2, ensure_ascii=False)}

Retorna JSON corregido manteniendo campos sin errores."""


__all__ = [
    "get_extraction_prompt",
    "get_extraction_prompt_cached",
    "get_validation_prompt",
    "get_correction_prompt"
]
