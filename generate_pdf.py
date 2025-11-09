#!/usr/bin/env python3
"""
Script para generar PDF de un consolidado.

Uso:
    python generate_pdf.py data/processed/802108003_consolidated.json
    python generate_pdf.py data/processed/*.consolidated.json
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.exporters.json_exporter import load_historia_from_json
from src.exporters.pdf_exporter import export_consolidated_to_pdf


def main():
    if len(sys.argv) < 2:
        print("Uso: python generate_pdf.py <archivo_consolidado.json>")
        print("\nEjemplo:")
        print("  python generate_pdf.py data/processed/802108003_consolidated.json")
        sys.exit(1)

    json_path = Path(sys.argv[1])

    if not json_path.exists():
        print(f"❌ Archivo no encontrado: {json_path}")
        sys.exit(1)

    print(f"\n📄 Generando PDF de: {json_path.name}\n")

    try:
        # Cargar historia
        print("1. Cargando JSON...")
        historia = load_historia_from_json(json_path)

        # Generar PDF
        print("2. Generando PDF...")
        pdf_path = export_consolidated_to_pdf(historia)

        print(f"\n✅ PDF generado exitosamente:")
        print(f"   {pdf_path}")

        # Mostrar resumen
        print(f"\n📊 Resumen del documento:")
        print(f"   Paciente: {historia.datos_empleado.nombre_completo}")
        print(f"   Documento: {historia.datos_empleado.documento}")
        print(f"   Diagnósticos: {len(historia.diagnosticos)}")
        print(f"   Exámenes: {len(historia.examenes)}")
        print(f"   Aptitud: {historia.aptitud_laboral}")
        print(f"   Alertas: {len(historia.alertas_validacion)}")
        print()

    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Instalar reportlab:")
        print("   pip install reportlab")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
