#!/bin/bash
# Script para validar todos los archivos procesados contra sus PDFs originales

echo "🔍 Validando todos los archivos procesados..."
echo ""

total=0
validados=0

for json_file in data/processed/*.json; do
    # Verificar que el archivo existe
    if [ ! -f "$json_file" ]; then
        continue
    fi

    total=$((total + 1))

    # Obtener el nombre base sin extensión
    filename=$(basename "$json_file" .json)
    pdf_file="data/raw/${filename}.pdf"

    # Verificar que el PDF existe
    if [ ! -f "$pdf_file" ]; then
        echo "⚠️  PDF no encontrado para: $filename"
        echo ""
        continue
    fi

    echo "📄 Validando: $filename"
    python validate_ground_truth.py "$pdf_file" "$json_file"
    validados=$((validados + 1))
    echo ""
    echo "-------------------------------------------"
    echo ""
done

echo "✅ Validación completada:"
echo "   Total procesados: $total"
echo "   Validados: $validados"
echo ""
echo "📊 Reportes generados en: data/labeled/"
