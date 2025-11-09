#!/usr/bin/env python3
"""
Script de validación de filtros centralizados.

Prueba los filtros de recomendaciones y alertas contra JSONs procesados
para validar que genéricas desaparecen y específicas se conservan.

Uso:
    python test_filters.py data/processed/802108003_consolidated.json
    python test_filters.py data/processed/*.json
"""

import json
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.processors.recommendation_filters import filter_recommendations
from src.processors.alert_filters import filter_alerts
from src.processors.validators import validate_historia_completa
from src.config.schemas import HistoriaClinicaEstructurada


def load_json_file(filepath: Path) -> dict:
    """Carga archivo JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_recommendation_filter(caso_id: str, historia_dict: dict):
    """Prueba filtro de recomendaciones."""
    print(f"\n{'='*80}")
    print(f"📋 Caso: {caso_id}")
    print(f"{'='*80}\n")

    recs_antes = historia_dict.get('recomendaciones', [])
    print(f"🔍 Recomendaciones ANTES del filtro: {len(recs_antes)}")

    if recs_antes:
        print("\nRecomendaciones actuales:")
        for i, rec in enumerate(recs_antes, 1):
            desc = rec.get('descripcion', '')
            print(f"  {i}. {desc[:80]}{'...' if len(desc) > 80 else ''}")

    # Aplicar nuevo filtro
    recs_despues = filter_recommendations(recs_antes, historia_dict)

    print(f"\n✅ Recomendaciones DESPUÉS del filtro: {len(recs_despues)}")
    print(f"❌ Eliminadas: {len(recs_antes) - len(recs_despues)}")

    if recs_despues:
        print("\nRecomendaciones conservadas:")
        for i, rec in enumerate(recs_despues, 1):
            desc = rec.get('descripcion', '')
            print(f"  {i}. {desc[:80]}{'...' if len(desc) > 80 else ''}")

    # Mostrar eliminadas
    eliminadas = [r for r in recs_antes if r not in recs_despues]
    if eliminadas:
        print(f"\n🗑️  Recomendaciones eliminadas ({len(eliminadas)}):")
        for i, rec in enumerate(eliminadas, 1):
            desc = rec.get('descripcion', '')
            print(f"  {i}. {desc[:80]}{'...' if len(desc) > 80 else ''}")


def test_alert_filter(caso_id: str, historia_dict: dict):
    """Prueba filtro de alertas."""
    print(f"\n{'='*80}")
    print(f"🚨 Alertas - Caso: {caso_id}")
    print(f"{'='*80}\n")

    # Convertir dict a HistoriaClinicaEstructurada para validación
    try:
        historia = HistoriaClinicaEstructurada.model_validate(historia_dict)
    except Exception as e:
        print(f"⚠️  Error validando schema: {e}")
        return

    # IMPORTANTE: Ejecutar validaciones para generar alertas frescas
    # (las alertas en el JSON pueden ser de una versión anterior del código)
    print("⚙️  Ejecutando validaciones (incluyendo cross-validation)...")
    alertas_generadas = validate_historia_completa(historia)

    # Combinar alertas del JSON + alertas generadas ahora
    alertas_antes = list(historia.alertas_validacion) + alertas_generadas
    print(f"🔍 Alertas ANTES del filtro: {len(alertas_antes)}")
    print(f"   - Del JSON: {len(historia.alertas_validacion)}")
    print(f"   - Generadas ahora: {len(alertas_generadas)}")

    if alertas_antes:
        print("\nAlertas actuales:")
        for i, alerta in enumerate(alertas_antes, 1):
            print(f"  {i}. [{alerta.tipo}] {alerta.descripcion[:70]}{'...' if len(alerta.descripcion) > 70 else ''}")

    # Aplicar nuevo filtro
    alertas_despues = filter_alerts(alertas_antes, historia)

    print(f"\n✅ Alertas DESPUÉS del filtro: {len(alertas_despues)}")
    print(f"❌ Eliminadas: {len(alertas_antes) - len(alertas_despues)}")

    if alertas_despues:
        print("\nAlertas conservadas:")
        for i, alerta in enumerate(alertas_despues, 1):
            print(f"  {i}. [{alerta.tipo}] {alerta.descripcion[:70]}{'...' if len(alerta.descripcion) > 70 else ''}")

    # Mostrar eliminadas
    eliminadas = [a for a in alertas_antes if a not in alertas_despues]
    if eliminadas:
        print(f"\n🗑️  Alertas eliminadas ({len(eliminadas)}):")
        for i, alerta in enumerate(eliminadas, 1):
            print(f"  {i}. [{alerta.tipo}] {alerta.descripcion[:70]}{'...' if len(alerta.descripcion) > 70 else ''}")


def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("❌ Error: Especifica al menos un archivo JSON")
        print("\nUso:")
        print("  python test_filters.py data/processed/802108003_consolidated.json")
        print("  python test_filters.py data/processed/*.json")
        sys.exit(1)

    archivos = [Path(arg) for arg in sys.argv[1:]]

    for archivo in archivos:
        if not archivo.exists():
            print(f"⚠️  Archivo no encontrado: {archivo}")
            continue

        print(f"\n\n{'#'*80}")
        print(f"# 📄 Procesando: {archivo.name}")
        print(f"{'#'*80}")

        try:
            historia_dict = load_json_file(archivo)
            caso_id = archivo.stem

            # Probar filtro de recomendaciones
            test_recommendation_filter(caso_id, historia_dict)

            # Probar filtro de alertas
            test_alert_filter(caso_id, historia_dict)

        except Exception as e:
            print(f"\n❌ Error procesando {archivo.name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n\n{'='*80}")
    print("✅ Pruebas completadas")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
