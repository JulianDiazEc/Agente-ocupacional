#!/bin/bash
# Script para validar todos los archivos procesados contra sus PDFs originales

# Elegir versión del validador
echo "🔍 Validador de Ground Truth"
echo ""
echo "¿Qué versión usar?"
echo "  [1] v1 - Validación básica (rápida)"
echo "  [2] v2 - Validación COMPLETA con razones (recomendada)"
echo ""
read -p "Selecciona versión [2]: " version
version=${version:-2}

if [ "$version" = "1" ]; then
    VALIDATOR="python validate_ground_truth.py"
    echo "✓ Usando validador v1 (básico)"
elif [ "$version" = "2" ]; then
    VALIDATOR="python validate_ground_truth_v2.py"
    echo "✓ Usando validador v2 (completo)"
else
    echo "❌ Opción inválida"
    exit 1
fi

echo ""
echo "📋 Validando todos los archivos procesados..."
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

    echo "📄 Validando: $filename"

    if [ "$version" = "1" ]; then
        # v1 requiere PDF específico
        pdf_file="data/raw/${filename}.pdf"

        if [ ! -f "$pdf_file" ]; then
            echo "⚠️  PDF no encontrado para: $filename"
            echo ""
            continue
        fi

        $VALIDATOR "$pdf_file" "$json_file"
    else
        # v2 auto-detecta PDFs desde el JSON
        $VALIDATOR "$json_file"
    fi

    validados=$((validados + 1))
    echo ""
    echo "-------------------------------------------"
    echo ""
done

echo "✅ Validación completada:"
echo "   Total procesados: $total"
echo "   Validados: $validados"
echo ""

if [ "$version" = "2" ]; then
    echo "📊 Reportes de correcciones en: data/labeled/*_corrections_report.json"
fi

echo "📁 Ground truth validado en: data/labeled/"
