#!/usr/bin/env python3
"""
Script para ver SOLO lo que extrae Azure, sin procesar con Claude.
Útil para debugging y verificar qué texto ve Claude.
"""

import sys
from pathlib import Path
from src.extractors.azure_extractor import AzureDocumentExtractor

if len(sys.argv) < 2:
    print("Uso: python extract_azure_only.py <archivo.pdf>")
    print("\nEjemplo:")
    print("  python extract_azure_only.py data/raw/HC_001.pdf")
    sys.exit(1)

pdf_path = Path(sys.argv[1])

if not pdf_path.exists():
    print(f"❌ Archivo no encontrado: {pdf_path}")
    sys.exit(1)

print(f"📄 Extrayendo texto de: {pdf_path.name}")
print("=" * 80)

extractor = AzureDocumentExtractor()
result = extractor.extract(pdf_path)

if not result.success:
    print(f"❌ Error: {result.error}")
    sys.exit(1)

print(f"✅ Extraídos {result.word_count} palabras ({result.page_count} páginas)")
print("=" * 80)
print("\nTEXTO EXTRAÍDO POR AZURE:\n")
print(result.text)
print("\n" + "=" * 80)

# Guardar a archivo
output_path = Path("data/processed") / f"{pdf_path.stem}_azure_extraction.txt"
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(result.text)

print(f"\n💾 Guardado en: {output_path}")
print(f"\nPara buscar términos específicos:")
print(f"  grep -i 'reasign' {output_path}")
print(f"  grep -i 'restriccion' {output_path}")
