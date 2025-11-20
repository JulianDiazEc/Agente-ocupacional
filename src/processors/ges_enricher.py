import json
from typing import Dict, Any, Optional, List
from pathlib import Path

def filter_clinical_alerts(hc_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filtra alertas clínicamente relevantes vs ruido administrativo
    """
    # Palabras clave de ruido administrativo
    administrative_noise = [
        "firma", "sello", "formato", "actualizar", "revisar", 
        "completar", "verificar", "documento", "archivo",
        "fecha de impresión", "número de historia", "datos del empleado"
    ]
    
    # Palabras clave de ruido técnico  
    technical_noise = [
        "calidad de imagen", "legibilidad", "escaneo", "pdf",
        "ocr", "extracción", "procesamiento"
    ]
    
    # Filtrar alertas si existen
    if "alertas" in hc_json:
        alertas_filtradas = []
        for alerta in hc_json["alertas"]:
            alerta_text = alerta.lower() if isinstance(alerta, str) else str(alerta).lower()
            
            # Verificar si es ruido
            is_noise = any(noise in alerta_text for noise in administrative_noise + technical_noise)
            
            if not is_noise:
                alertas_filtradas.append(alerta)
        
        hc_json["alertas"] = alertas_filtradas
    
    return hc_json

def consolidate_duplicate_diagnoses(hc_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Consolida diagnósticos duplicados priorizando por CIE-10
    """
    diagnosticos = hc_json.get("diagnosticos", [])
    if not diagnosticos:
        return hc_json
    
    # Agrupar por código CIE-10 o descripción similar
    consolidated = {}
    
    for diag in diagnosticos:
        codigo = diag.get("codigo_cie10")
        descripcion = diag.get("descripcion", "").upper().strip()
        
        if codigo:
            # Priorizar diagnósticos con código CIE-10
            key = f"CIE_{codigo}"
            if key not in consolidated or consolidated[key].get("confianza", 0) < diag.get("confianza", 0):
                consolidated[key] = diag
        else:
            # Agrupar descripciones similares (evitar duplicados)
            key = f"DESC_{descripcion[:30]}"  # Primeras 30 chars como clave
            if key not in consolidated:
                consolidated[key] = diag
    
    hc_json["diagnosticos"] = list(consolidated.values())
    return hc_json

def enrich_hc_with_ges_context(hc_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriquece la historia clínica con contexto específico del GES del cargo.
    
    Args:
        hc_json: Historia clínica consolidada
        
    Returns:
        Historia clínica enriquecida con contexto GES
    """
    # PASO 1: FILTROS DE LIMPIEZA
    hc_json = filter_clinical_alerts(hc_json)
    hc_json = consolidate_duplicate_diagnoses(hc_json)
    
    # Extraer datos del empleado
    datos_empleado = hc_json.get("datos_empleado", {})
    empresa = datos_empleado.get("empresa", "").strip()
    cargo = datos_empleado.get("cargo", "").strip().lower()
    
    if not empresa or not cargo:
        return hc_json
    
    # Cargar data.json
    config_path = Path(__file__).parent.parent / "config" / "empresas" / "data.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return hc_json
    
    # Buscar GES que contenga el cargo
    ges_match = None
    for ges in data.get("ges", []):
        if not ges.get("activo", True):
            continue
            
        # Verificar si el cargo está en la lista de cargos del GES
        cargos_ges = [c.strip().lower() for c in ges.get("cargos", [])]
        if cargo in cargos_ges:
            ges_match = ges
            break
    
    if ges_match:
        # ✅ USAR DIRECTAMENTE examenes_incluidos (ya está limpio)
        examenes_obligatorios = extract_mandatory_exams_from_ges(ges_match)
        
        hc_json["contexto_ges"] = {
            "id": ges_match.get("id"),
            "nombre": ges_match.get("nombre"),
            "descripcion": ges_match.get("descripcion", ""),
            "peligros_principales": ges_match.get("peligros_principales", []),
            "examenes_incluidos": ges_match.get("examenes_incluidos", []),  # Original
            "examenes_obligatorios": examenes_obligatorios,  # ✅ MISMO CONTENIDO, solo limpiado
            "criterios_clinicos": ges_match.get("criterios_clinicos", ""),
            "relacion_examenes": ges_match.get("relacion_examenes", ""),
        }
    
    return hc_json

# Función de testing mejorada
def test_ges_enricher():
    """
    Test del enriquecedor GES con datos reales
    """
    sample_hc = {
        "datos_empleado": {
            "empresa": "Fundacion Ser Social",
            "cargo": "auxiliar administrativo"  # Este cargo existe en tu GES 3
        },
        "alertas": [
            "Falta firma del médico",
            "HTA no controlada requiere seguimiento", 
            "Documento sin sello"
        ],
        "diagnosticos": [
            {"codigo_cie10": "M54.5", "descripcion": "LUMBALGIA", "confianza": 1.0},
            {"codigo_cie10": None, "descripcion": "Dolor lumbar", "confianza": 0.8}
        ]
    }
    
    result = enrich_hc_with_ges_context(sample_hc)
    
    print("=== RESULTADO DEL ENRIQUECIMIENTO ===")
    print(f"Alertas filtradas: {result.get('alertas', [])}")
    print(f"Diagnósticos consolidados: {len(result.get('diagnosticos', []))}")
    
    contexto_ges = result.get('contexto_ges', {})
    if contexto_ges:
        print(f"GES encontrado: {contexto_ges.get('nombre')}")
        print(f"Peligros: {contexto_ges.get('peligros_principales')}")
        print(f"Exámenes obligatorios: {contexto_ges.get('examenes_obligatorios')}")
    else:
        print("No se encontró GES para el cargo")

# Para probar: test_ges_enricher()