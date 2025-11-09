#!/usr/bin/env python3
"""
Prueba simple del consolidado con validaciones.

Crea 2 JSONs sintéticos:
1. HC con diagnóstico de miopía + optometría normal (inconsistencia)
2. Examen con audiometría crítica sin reflejo en dx/recs

Verifica que el consolidado genere las alertas esperadas.
"""

from consolidate_person import consolidate_historias

# JSON 1: HC con diagnóstico visual + examen normal (inconsistencia)
hc = {
    "tipo_documento_fuente": "hc_completa",
    "archivo_origen": "hc_test.json",
    "datos_empleado": {
        "nombre_completo": "Juan Test",
        "documento": "123456789"
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
            "resultado": "Visión 20/20 con corrección óptica",
            "hallazgos_clave": "Visión corregida normal bilateral"
        }
    ],
    "antecedentes": [],
    "recomendaciones": [],
    "restricciones_especificas": None,
    "signos_vitales": None,
    "alertas_validacion": [],
    "programas_sve": []
}

# JSON 2: Examen específico con hallazgo crítico SIN reflejo
examen = {
    "tipo_documento_fuente": "examen_especifico",
    "archivo_origen": "audiometria_test.json",
    "datos_empleado": {
        "nombre_completo": "Juan Test",
        "documento": "123456789"
    },
    "diagnosticos": [],  # ❌ Sin diagnóstico
    "examenes": [
        {
            "tipo": "audiometria",
            "nombre": "Audiometría tonal",
            "fecha_realizacion": "2024-11-01",
            "interpretacion": "critico",  # ✅ Crítico
            "resultado": "Hipoacusia bilateral severa",
            "hallazgos_clave": "Pérdida auditiva >60dB en frecuencias 4000-8000 Hz bilateral"
        }
    ],
    "antecedentes": [],
    "recomendaciones": [],  # ❌ Sin recomendaciones
    "restricciones_especificas": None,  # ❌ Sin restricciones
    "signos_vitales": None,
    "alertas_validacion": [],
    "programas_sve": []
}

print("=" * 80)
print("TEST: Consolidado con Validaciones")
print("=" * 80)

# Consolidar
print("\n🔄 Consolidando 2 documentos...")
consolidado = consolidate_historias([hc, examen])

# Verificar resultado
print(f"\n✅ Tipo documento: {consolidado['tipo_documento_fuente']}")
print(f"📊 Diagnósticos: {len(consolidado['diagnosticos'])}")
print(f"🔬 Exámenes en consolidado: {len(consolidado['examenes'])}")
print(f"⚠️  Alertas generadas: {len(consolidado['alertas_validacion'])}")

if consolidado['alertas_validacion']:
    print("\n" + "=" * 80)
    print("ALERTAS GENERADAS:")
    print("=" * 80)
    for i, alerta in enumerate(consolidado['alertas_validacion'], 1):
        print(f"\n{i}. [{alerta['tipo']}] Severidad: {alerta['severidad']}")
        print(f"   Campo: {alerta['campo_afectado']}")
        print(f"   Descripción: {alerta['descripcion']}")
        print(f"   Acción: {alerta['accion_sugerida']}")
else:
    print("\n❌ NO SE GENERARON ALERTAS (PROBLEMA)")

print("\n" + "=" * 80)
print("ALERTAS ESPERADAS:")
print("=" * 80)
print("1. inconsistencia_diagnostica: Miopía pero optometría normal")
print("2. inconsistencia_diagnostica: Audiometría crítica sin reflejo en dx/recs/restricciones")
print("\n")
