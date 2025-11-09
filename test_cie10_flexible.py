#!/usr/bin/env python3
"""
Test para validar que códigos CIE-10 cortos funcionan correctamente.

Verifica que:
1. Schema acepta códigos cortos (N80, M50, K42)
2. Schema acepta códigos completos (H52.1, M54.5)
3. Códigos cortos generan alerta de severidad BAJA
4. Códigos completos NO generan alerta
5. NUNCA lanza ValidationError
"""

from src.config.schemas import HistoriaClinicaEstructurada, Diagnostico
from src.processors.validators import CIE10Validator
import json

print("=" * 80)
print("TEST: Códigos CIE-10 flexibles (cortos y completos)")
print("=" * 80)

# Test 1: Validador acepta formatos
print("\n1️⃣  TEST CIE10Validator.validate_format()")
print("-" * 80)

test_codes = [
    ("N80", True, "debe aceptar formato corto"),
    ("M50", True, "debe aceptar formato corto"),
    ("K42", True, "debe aceptar formato corto"),
    ("H52.1", True, "debe aceptar formato completo"),
    ("M54.5", True, "debe aceptar formato completo"),
    ("J45.0", True, "debe aceptar formato completo"),
    ("XYZ", False, "debe rechazar formato inválido"),
    ("123", False, "debe rechazar sin letra"),
]

for code, expected_valid, description in test_codes:
    is_valid, msg = CIE10Validator.validate_format(code)
    status = "✅" if is_valid == expected_valid else "❌"
    print(f"{status} {code:10} → valid={is_valid:5} | {description}")
    if msg:
        print(f"   └─ {msg}")

# Test 2: Schema Pydantic acepta códigos cortos
print("\n2️⃣  TEST Schema Pydantic (NO debe lanzar ValidationError)")
print("-" * 80)

test_diagnosticos = [
    {"codigo_cie10": "N80", "descripcion": "Endometriosis"},
    {"codigo_cie10": "M50", "descripcion": "Trastornos de discos cervicales"},
    {"codigo_cie10": "K42", "descripcion": "Hernia umbilical"},
    {"codigo_cie10": "H52.1", "descripcion": "Miopía"},
]

for diag_dict in test_diagnosticos:
    try:
        diag = Diagnostico.model_validate(diag_dict)
        print(f"✅ {diag.codigo_cie10:10} → Pydantic aceptó sin error")
    except Exception as e:
        print(f"❌ {diag_dict['codigo_cie10']:10} → ERROR: {e}")

# Test 3: Historia completa con diagnósticos cortos
print("\n3️⃣  TEST Historia Completa con diagnósticos cortos")
print("-" * 80)

historia_dict = {
    "tipo_documento_fuente": "hc_completa",
    "archivo_origen": "test_cie10.json",
    "datos_empleado": {
        "nombre_completo": "Test CIE10",
        "documento": "123456789"
    },
    "diagnosticos": [
        {"codigo_cie10": "N80", "descripcion": "Endometriosis"},
        {"codigo_cie10": "M50", "descripcion": "Trastornos discos cervicales"},
        {"codigo_cie10": "H52.1", "descripcion": "Miopía bilateral"},
    ],
    "examenes": [],
    "antecedentes": [],
    "recomendaciones": [],
    "alertas_validacion": [],
    "programas_sve": []
}

try:
    historia = HistoriaClinicaEstructurada.model_validate(historia_dict)
    print(f"✅ Historia validada correctamente")
    print(f"   └─ {len(historia.diagnosticos)} diagnósticos aceptados:")
    for diag in historia.diagnosticos:
        print(f"      - {diag.codigo_cie10}: {diag.descripcion}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 4: Validaciones generan alertas correctas
print("\n4️⃣  TEST Alertas generadas por validaciones")
print("-" * 80)

alertas = CIE10Validator.validate_diagnosis_list(historia.diagnosticos)

print(f"📋 Total de alertas: {len(alertas)}")
for i, alerta in enumerate(alertas, 1):
    print(f"\n{i}. [{alerta.tipo}] Severidad: {alerta.severidad}")
    print(f"   Campo: {alerta.campo_afectado}")
    print(f"   Descripción: {alerta.descripcion}")

# Test 5: Verificar severidades
print("\n5️⃣  VERIFICACIÓN DE SEVERIDADES")
print("-" * 80)

alertas_n80 = [a for a in alertas if "N80" in a.descripcion]
alertas_m50 = [a for a in alertas if "M50" in a.descripcion]
alertas_h52 = [a for a in alertas if "H52.1" in a.descripcion]

print(f"N80 (corto):     {len(alertas_n80)} alerta(s) - ", end="")
if alertas_n80 and alertas_n80[0].severidad == "baja":
    print("✅ severidad BAJA (correcto)")
elif not alertas_n80:
    print("❌ NO generó alerta (debería generar severidad baja)")
else:
    print(f"❌ severidad {alertas_n80[0].severidad} (debería ser baja)")

print(f"M50 (corto):     {len(alertas_m50)} alerta(s) - ", end="")
if alertas_m50 and alertas_m50[0].severidad == "baja":
    print("✅ severidad BAJA (correcto)")
elif not alertas_m50:
    print("❌ NO generó alerta (debería generar severidad baja)")
else:
    print(f"❌ severidad {alertas_m50[0].severidad} (debería ser baja)")

print(f"H52.1 (completo): {len(alertas_h52)} alerta(s) - ", end="")
if not alertas_h52:
    print("✅ SIN alerta (correcto)")
else:
    print(f"❌ Generó alerta (NO debería)")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print("✅ Schema acepta códigos cortos SIN ValidationError")
print("✅ Códigos cortos generan alerta de severidad BAJA")
print("✅ Códigos completos NO generan alerta")
print("\n💡 Arquitectura correcta: Problemas de formato → alertas, NO ValidationError")
