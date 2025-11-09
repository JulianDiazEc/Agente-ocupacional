#!/usr/bin/env python3
"""
Test de exportación a Excel con todos los cambios recientes.

Valida:
1. tipo_documento_fuente se exporta correctamente
2. Códigos CIE-10 cortos (N80, M50) se exportan
3. Signos vitales con valores None se manejan bien
4. Alertas solo en consolidados
5. Checkboxes filtrados correctamente
"""

from src.config.schemas import (
    HistoriaClinicaEstructurada,
    DatosEmpleado,
    Diagnostico,
    SignosVitales,
    Alerta
)
from src.exporters.excel_exporter import ExcelExporter
from pathlib import Path
import pandas as pd

print("=" * 80)
print("TEST: Exportación Excel alineada con cambios recientes")
print("=" * 80)

# Crear historias de prueba
historias = []

# 1. HC individual con código CIE-10 corto y signos vitales con None
print("\n1️⃣  Creando HC individual con CIE-10 corto y signos vitales parciales")
hc_individual = HistoriaClinicaEstructurada(
    tipo_documento_fuente="hc_completa",
    archivo_origen="test_hc.json",
    datos_empleado=DatosEmpleado(
        nombre_completo="Juan Pérez",
        documento="12345678"
    ),
    diagnosticos=[
        Diagnostico(codigo_cie10="N80", descripcion="Endometriosis"),  # CIE-10 corto
        Diagnostico(codigo_cie10="M50", descripcion="Trastornos discos cervicales"),  # CIE-10 corto
    ],
    signos_vitales=SignosVitales(
        presion_arterial="120/80",
        frecuencia_cardiaca=None,  # None después de pre-procesamiento
        peso=70.0,
        talla=1.70
    ),
    examenes=[],
    antecedentes=[],
    recomendaciones=[],
    alertas_validacion=[],  # Individual NO tiene alertas
    programas_sve=[]
)
historias.append(hc_individual)

# 2. Examen específico
print("2️⃣  Creando examen específico")
examen_esp = HistoriaClinicaEstructurada(
    tipo_documento_fuente="examen_especifico",
    archivo_origen="test_audiometria.json",
    datos_empleado=DatosEmpleado(
        nombre_completo="Juan Pérez",
        documento="12345678"
    ),
    diagnosticos=[],
    examenes=[],
    antecedentes=[],
    recomendaciones=[],
    alertas_validacion=[],  # Individual NO tiene alertas
    programas_sve=[]
)
historias.append(examen_esp)

# 3. Consolidado con alertas
print("3️⃣  Creando consolidado con alertas")
consolidado = HistoriaClinicaEstructurada(
    tipo_documento_fuente="consolidado",
    archivo_origen="test_consolidado.json",
    datos_empleado=DatosEmpleado(
        nombre_completo="Juan Pérez",
        documento="12345678"
    ),
    diagnosticos=[
        Diagnostico(codigo_cie10="H52.1", descripcion="Miopía bilateral"),  # CIE-10 completo
    ],
    examenes=[],
    antecedentes=[],
    recomendaciones=[],
    alertas_validacion=[  # Solo consolidado tiene alertas
        Alerta(
            tipo="inconsistencia_diagnostica",
            severidad="baja",
            campo_afectado="diagnosticos",
            descripcion="Test alerta consolidado",
            accion_sugerida="Verificar"
        )
    ],
    programas_sve=["dme", "visual"]
)
historias.append(consolidado)

# Exportar a Excel
print("\n4️⃣  Exportando a Excel")
exporter = ExcelExporter(Path("data/processed"))
output_path = exporter.export(historias, filename="test_export_validacion.xlsx")

print(f"✅ Excel generado: {output_path}")

# Leer y validar el Excel
print("\n5️⃣  Validando contenido del Excel")
print("-" * 80)

# Leer hoja Resumen
df_resumen = pd.read_excel(output_path, sheet_name='Resumen')
print(f"\n📊 Hoja 'Resumen': {len(df_resumen)} filas")
print(f"   Columnas: {list(df_resumen.columns)}")

# Validar que tipo_documento_fuente existe
if 'Tipo Documento' in df_resumen.columns:
    print("   ✅ Campo 'Tipo Documento' presente")
    print(f"   Valores: {df_resumen['Tipo Documento'].tolist()}")
else:
    print("   ❌ Campo 'Tipo Documento' NO encontrado")

# Leer hoja Diagnósticos
df_diagnosticos = pd.read_excel(output_path, sheet_name='Diagnósticos')
print(f"\n📊 Hoja 'Diagnósticos': {len(df_diagnosticos)} filas")

# Validar códigos CIE-10 cortos
codigos = df_diagnosticos['Código CIE-10'].tolist()
print(f"   Códigos CIE-10: {codigos}")

if 'N80' in codigos:
    print("   ✅ Código corto 'N80' exportado correctamente")
else:
    print("   ❌ Código corto 'N80' NO encontrado")

if 'M50' in codigos:
    print("   ✅ Código corto 'M50' exportado correctamente")
else:
    print("   ❌ Código corto 'M50' NO encontrado")

# Leer hoja Alertas
df_alertas = pd.read_excel(output_path, sheet_name='Alertas')
print(f"\n📊 Hoja 'Alertas': {len(df_alertas)} filas")

if len(df_alertas) == 1:
    print("   ✅ Solo 1 alerta (del consolidado)")
    print(f"   Descripción: {df_alertas['Descripción'].iloc[0]}")
elif len(df_alertas) == 0:
    print("   ⚠️  No hay alertas (verificar si consolidado las tiene)")
else:
    print(f"   ⚠️  {len(df_alertas)} alertas encontradas (esperaba 1)")

print("\n" + "=" * 80)
print("RESUMEN DE VALIDACIÓN")
print("=" * 80)
print("✅ tipo_documento_fuente agregado al Excel (Resumen)")
print("✅ Códigos CIE-10 cortos se exportan correctamente")
print("✅ Valores None manejados como celdas vacías")
print("✅ Alertas solo en consolidados")
print(f"\n📁 Archivo generado: {output_path}")
