#!/usr/bin/env python3
"""
Script de prueba para validación cruzada diagnóstico↔examen.

Prueba con datos sintéticos para verificar que la lógica funciona.
Valida SOLO en HC completa y CMO (NO en consolidado ni examen específico).
"""

from datetime import date
from src.config.schemas import (
    HistoriaClinicaEstructurada,
    Diagnostico,
    Examen,
    DatosEmpleado
)
from src.processors.validators import validate_diagnosis_exam_consistency

print("=" * 80)
print("TEST: Validación Cruzada Diagnóstico↔Examen")
print("=" * 80)

# Test 1: Visual - Miopía con visión 20/20
print("\n1️⃣ Test Visual: Miopía + Optometría normal")
print("-" * 80)

historia_visual = HistoriaClinicaEstructurada(
    archivo_origen="test_visual.pdf",
    tipo_documento_fuente="hc_completa",  # ← Valida en HC completa
    datos_empleado=DatosEmpleado(nombre_completo="Test Visual"),
    diagnosticos=[
        Diagnostico(
            codigo_cie10="H52.1",
            descripcion="Miopía bilateral",
            tipo="principal"
        )
    ],
    examenes=[
        Examen(
            tipo="optometria",
            nombre="Optometría ocupacional",
            resultado="Visión 20/20 con corrección óptica",
            hallazgos_clave="Agudeza visual corregida normal bilateral"
        )
    ]
)

alertas_visual = validate_diagnosis_exam_consistency(historia_visual)
print(f"Alertas generadas: {len(alertas_visual)}")
for alerta in alertas_visual:
    print(f"  - Tipo: {alerta.tipo}")
    print(f"  - Severidad: {alerta.severidad}")
    print(f"  - Descripción: {alerta.descripcion}")
    print(f"  - Acción: {alerta.accion_sugerida}")

# Test 2: Auditivo - Hipoacusia con audiometría normal
print("\n2️⃣ Test Auditivo: Hipoacusia + Audiometría normal")
print("-" * 80)

historia_auditiva = HistoriaClinicaEstructurada(
    archivo_origen="test_auditivo.pdf",
    tipo_documento_fuente="hc_completa",
    datos_empleado=DatosEmpleado(nombre_completo="Test Auditivo"),
    diagnosticos=[
        Diagnostico(
            codigo_cie10="H90.3",
            descripcion="Hipoacusia neurosensorial bilateral",
            tipo="principal"
        )
    ],
    examenes=[
        Examen(
            tipo="audiometria",
            nombre="Audiometría tonal",
            resultado="Audición normal bilateral",
            hallazgos_clave="Umbrales auditivos dentro de límites normales"
        )
    ]
)

alertas_auditivas = validate_diagnosis_exam_consistency(historia_auditiva)
print(f"Alertas generadas: {len(alertas_auditivas)}")
for alerta in alertas_auditivas:
    print(f"  - Tipo: {alerta.tipo}")
    print(f"  - Severidad: {alerta.severidad}")
    print(f"  - Descripción: {alerta.descripcion}")

# Test 3: Respiratorio - EPOC con espirometría normal
print("\n3️⃣ Test Respiratorio: EPOC + Espirometría normal")
print("-" * 80)

historia_respiratoria = HistoriaClinicaEstructurada(
    archivo_origen="test_respiratorio.pdf",
    tipo_documento_fuente="hc_completa",
    datos_empleado=DatosEmpleado(nombre_completo="Test Respiratorio"),
    diagnosticos=[
        Diagnostico(
            codigo_cie10="J44.0",
            descripcion="EPOC con infección aguda de vías respiratorias inferiores",
            tipo="principal"
        )
    ],
    examenes=[
        Examen(
            tipo="espirometria",
            nombre="Espirometría forzada",
            resultado="Función pulmonar normal",
            hallazgos_clave="FEV1 normal, FVC normal, sin obstrucción"
        )
    ]
)

alertas_respiratorias = validate_diagnosis_exam_consistency(historia_respiratoria)
print(f"Alertas generadas: {len(alertas_respiratorias)}")
for alerta in alertas_respiratorias:
    print(f"  - Tipo: {alerta.tipo}")
    print(f"  - Severidad: {alerta.severidad}")
    print(f"  - Descripción: {alerta.descripcion}")

# Test 4: Examen específico - No debe generar alertas
print("\n4️⃣ Test Control: Examen específico - NO debe generar alertas")
print("-" * 80)

historia_examen_especifico = HistoriaClinicaEstructurada(
    archivo_origen="test_examen.pdf",
    tipo_documento_fuente="examen_especifico",  # ← NO valida cross-validation
    datos_empleado=DatosEmpleado(nombre_completo="Test Examen"),
    diagnosticos=[
        Diagnostico(
            codigo_cie10="H52.1",
            descripcion="Miopía bilateral",
            tipo="principal"
        )
    ],
    examenes=[
        Examen(
            tipo="optometria",
            nombre="Optometría ocupacional",
            resultado="Visión 20/20 con corrección óptica"
        )
    ]
)

alertas_examen = validate_diagnosis_exam_consistency(historia_examen_especifico)
print(f"Alertas generadas: {len(alertas_examen)} (debe ser 0)")

# Test 5: Sin examen - No debe generar alerta
print("\n5️⃣ Test Control: Diagnóstico sin examen - NO debe generar alertas")
print("-" * 80)

historia_sin_examen = HistoriaClinicaEstructurada(
    archivo_origen="test_sin_examen.pdf",
    tipo_documento_fuente="hc_completa",
    datos_empleado=DatosEmpleado(nombre_completo="Test Sin Examen"),
    diagnosticos=[
        Diagnostico(
            codigo_cie10="H52.1",
            descripcion="Miopía bilateral",
            tipo="principal"
        )
    ],
    examenes=[]  # Sin exámenes
)

alertas_sin_examen = validate_diagnosis_exam_consistency(historia_sin_examen)
print(f"Alertas generadas: {len(alertas_sin_examen)} (debe ser 0)")

# Resumen
print("\n" + "=" * 80)
print("RESUMEN DE TESTS")
print("=" * 80)
print(f"1. Visual (miopía + optometría normal): {len(alertas_visual)} alertas (esperado: 1)")
print(f"2. Auditivo (hipoacusia + audiometría normal): {len(alertas_auditivas)} alertas (esperado: 1)")
print(f"3. Respiratorio (EPOC + espirometría normal): {len(alertas_respiratorias)} alertas (esperado: 1)")
print(f"4. Examen específico (NO debe validar): {len(alertas_examen)} alertas (esperado: 0)")
print(f"5. Sin examen: {len(alertas_sin_examen)} alertas (esperado: 0)")

total_esperado = 3
total_obtenido = len(alertas_visual) + len(alertas_auditivas) + len(alertas_respiratorias)

if total_obtenido == total_esperado:
    print("\n✅ TODOS LOS TESTS PASARON")
else:
    print(f"\n❌ TESTS FALLARON: Esperado {total_esperado}, obtenido {total_obtenido}")
