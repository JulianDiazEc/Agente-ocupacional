#!/bin/bash
# Script para corregir imports incorrectos de settings y limpiar caché de Python

echo "🔍 Buscando imports incorrectos de settings..."

# Buscar el patrón incorrecto
FILES_WITH_ERROR=$(find . -name "*.py" -type f ! -path "*/__pycache__/*" ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/venv/*" -exec grep -l "from src.config.settings import settings$" {} \; 2>/dev/null)

if [ -z "$FILES_WITH_ERROR" ]; then
    echo "✅ No se encontraron imports incorrectos"
else
    echo "❌ Archivos con import incorrecto:"
    echo "$FILES_WITH_ERROR"
    echo ""
    echo "🔧 Corrigiendo automáticamente..."

    # Corregir cada archivo
    for file in $FILES_WITH_ERROR; do
        # Backup
        cp "$file" "$file.bak"

        # Reemplazar el import incorrecto
        sed -i.tmp 's/from src\.config\.settings import settings$/from src.config.settings import get_settings/g' "$file"
        rm -f "$file.tmp"

        echo "  ✅ Corregido: $file"
    done

    echo ""
    echo "⚠️  IMPORTANTE: Debes actualizar el uso de settings en estos archivos:"
    echo "   Antes:"
    echo "     settings.azure_doc_intelligence_endpoint"
    echo ""
    echo "   Después:"
    echo "     settings = get_settings()"
    echo "     settings.azure_doc_intelligence_endpoint"
fi

echo ""
echo "🧹 Limpiando archivos compilados de Python..."

# Limpiar __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Limpiar .pyc
find . -type f -name "*.pyc" -delete 2>/dev/null

# Limpiar .pyo
find . -type f -name "*.pyo" -delete 2>/dev/null

echo "✅ Caché de Python limpiado"

echo ""
echo "🎉 Proceso completado. Intenta ejecutar tu aplicación nuevamente."
