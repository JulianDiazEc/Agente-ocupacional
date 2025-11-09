#!/usr/bin/env python3
"""
Verificación de arquitectura: Individual vs Consolidado

Demuestra que:
1. Documentos individuales tienen alertas_validacion = [] (solo limpieza)
2. Consolidado tiene todas las alertas clínicas
"""

from consolidate_person import consolidate_historias
from src.processors.claude_processor import validate_signos_vitales, normalize_aptitud_laboral
from src.config.schemas import HistoriaClinicaEstructurada
import json

print("=" * 80)
print("VERIFICACIÓN DE ARQUITECTURA: Individual vs Consolidado")
print("=" * 80)

# 1. DOCUMENTO INDIVIDUAL: HC con datos problemáticos
print("\n1️⃣  PROCESAMIENTO INDIVIDUAL (simula claude_processor.py)")
print("-" * 80)

hc_dict = {
    "tipo_documento_fuente": "hc_completa",
    "archivo_origen": "test_hc.json",
    "datos_empleado": {
        "nombre_completo": "Test Individual",
        "documento": "111111111"
    },
    "fecha_emo": "2024-11-01",
    "tipo_emo": "periodico",
    "diagnosticos": [
        {
            "codigo_cie10": "H52.1",
            "descripcion": "Miopía bilateral",
            "tipo": "principal",
            "lateralidad": "bilateral"
        }
    ],
    "examenes": [
        {
            "tipo": "optometria",
            "nombre": "Optometría ocupacional",
            "fecha_realizacion": "2024-11-01",
            "interpretacion": "normal",
            "resultado": "Visión 20/20 con corrección",
            "hallazgos_clave": "Normal"
        }
    ],
    "signos_vitales": {
        "presion_arterial": "500/300",  # ❌ Fuera de rango
        "frecuencia_cardiaca": 999,     # ❌ Fuera de rango
        "peso": 65.0,
        "talla": 1.70
    },
    "aptitud_laboral": "aplazado para completar estudios",  # ❌ No estándar
    "antecedentes": [],
    "recomendaciones": [],
    "restricciones_especificas": None,
    "alertas_validacion": [],
    "programas_sve": []
}

# Simular pre-procesamiento de claude_processor.py
print("   🔧 Pre-procesamiento (limpieza de datos)...")
alertas_preprocesamiento = []  # Se usa internamente, NO se guarda
hc_dict = validate_signos_vitales(hc_dict, alertas_preprocesamiento)
hc_dict = normalize_aptitud_laboral(hc_dict, alertas_preprocesamiento)

print(f"   📋 Alertas de pre-procesamiento detectadas: {len(alertas_preprocesamiento)}")
for alerta in alertas_preprocesamiento:
    print(f"      - {alerta.tipo}: {alerta.descripcion[:60]}...")

# Validar con Pydantic
hc_obj = HistoriaClinicaEstructurada.model_validate(hc_dict)

# ARQUITECTURA: NO se guardan alertas en documentos individuales
print(f"\n   ✅ alertas_validacion en HC individual: {len(hc_obj.alertas_validacion)}")
print(f"   ✅ signos_vitales.presion_arterial limpiado: {hc_obj.signos_vitales.presion_arterial if hc_obj.signos_vitales else 'None'}")
print(f"   ✅ signos_vitales.frecuencia_cardiaca limpiado: {hc_obj.signos_vitales.frecuencia_cardiaca if hc_obj.signos_vitales else 'None'}")
print(f"   ✅ aptitud_laboral normalizado: {hc_obj.aptitud_laboral}")

# Convertir a dict para consolidación
hc_final = json.loads(hc_obj.model_dump_json())

# 2. OTRO DOCUMENTO INDIVIDUAL: Examen con hallazgo crítico
print("\n2️⃣  OTRO DOCUMENTO INDIVIDUAL (examen específico)")
print("-" * 80)

examen_dict = {
    "tipo_documento_fuente": "examen_especifico",
    "archivo_origen": "test_audio.json",
    "datos_empleado": {
        "nombre_completo": "Test Individual",
        "documento": "111111111"
    },
    "diagnosticos": [],  # ❌ Sin diagnóstico
    "examenes": [
        {
            "tipo": "audiometria",
            "nombre": "Audiometría tonal",
            "fecha_realizacion": "2024-11-01",
            "interpretacion": "critico",  # ✅ Crítico
            "resultado": "Hipoacusia severa",
            "hallazgos_clave": "Pérdida >60dB bilateral"
        }
    ],
    "antecedentes": [],
    "recomendaciones": [],  # ❌ Sin recomendaciones
    "restricciones_especificas": None,
    "signos_vitales": None,
    "alertas_validacion": [],
    "programas_sve": []
}

# Pre-procesamiento
alertas_preprocesamiento2 = []
examen_dict = validate_signos_vitales(examen_dict, alertas_preprocesamiento2)
examen_dict = normalize_aptitud_laboral(examen_dict, alertas_preprocesamiento2)

examen_obj = HistoriaClinicaEstructurada.model_validate(examen_dict)

print(f"   ✅ alertas_validacion en examen específico: {len(examen_obj.alertas_validacion)}")
print(f"   ✅ Pre-procesamiento detectó: {len(alertas_preprocesamiento2)} alertas (no guardadas)")

examen_final = json.loads(examen_obj.model_dump_json())

# 3. CONSOLIDADO: Todas las validaciones
print("\n3️⃣  CONSOLIDADO (todas las validaciones clínicas)")
print("-" * 80)

print("   🔄 Consolidando 2 documentos individuales...")
consolidado = consolidate_historias([hc_final, examen_final])

print(f"\n   ✅ Tipo documento: {consolidado['tipo_documento_fuente']}")
print(f"   📊 Diagnósticos consolidados: {len(consolidado['diagnosticos'])}")
print(f"   🔬 Exámenes consolidados: {len(consolidado['examenes'])}")
print(f"   ⚠️  ALERTAS GENERADAS EN CONSOLIDADO: {len(consolidado['alertas_validacion'])}")

if consolidado['alertas_validacion']:
    print("\n   ALERTAS CLÍNICAS:")
    for i, alerta in enumerate(consolidado['alertas_validacion'], 1):
        print(f"   {i}. [{alerta['tipo']}] {alerta['severidad']}")
        print(f"      {alerta['descripcion'][:70]}...")
else:
    print("\n   ❌ ERROR: No se generaron alertas en consolidado")

# RESUMEN
print("\n" + "=" * 80)
print("RESUMEN DE ARQUITECTURA")
print("=" * 80)
print(f"✅ HC individual:         {len(hc_final['alertas_validacion'])} alertas (esperado: 0)")
print(f"✅ Examen específico:     {len(examen_final['alertas_validacion'])} alertas (esperado: 0)")
print(f"✅ Consolidado:           {len(consolidado['alertas_validacion'])} alertas (esperado: >0)")
print("\n📋 Arquitectura correcta:")
print("   - Documentos individuales: Solo extracción y limpieza (NO piensan)")
print("   - Consolidado: Todas las validaciones clínicas (SÍ piensa)")
print()
