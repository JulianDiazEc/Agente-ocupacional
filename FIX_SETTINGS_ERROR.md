# Solución para el Error de Importación de Settings

## El Error

```
ImportError: cannot import name 'settings' from 'src.config.settings'
```

## Causa

El archivo `src/config/settings.py` NO exporta una variable llamada `settings`. Solo exporta:
- `Settings` (la clase)
- `get_settings()` (función para obtener la instancia singleton)
- `reload_settings()` (función para recargar configuración)

## Solución Rápida

### Opción 1: Script Automático

Ejecuta el script de corrección:

```bash
cd /Users/juliandiaz/Agentes/Medico/Agente-ocupacional
./fix_settings_import.sh
```

Este script:
1. Busca todos los imports incorrectos
2. Los corrige automáticamente
3. Limpia archivos compilados de Python (.pyc, __pycache__)

### Opción 2: Corrección Manual

1. **Busca el archivo con el import incorrecto:**

```bash
grep -r "from src.config.settings import settings" --include="*.py" .
```

2. **Reemplaza el import:**

```python
# ❌ INCORRECTO
from src.config.settings import settings

# ✅ CORRECTO
from src.config.settings import get_settings
```

3. **Actualiza el uso de settings:**

```python
# ❌ INCORRECTO
endpoint = settings.azure_doc_intelligence_endpoint

# ✅ CORRECTO
settings = get_settings()
endpoint = settings.azure_doc_intelligence_endpoint
```

4. **Limpia archivos compilados:**

```bash
# Limpiar __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Limpiar .pyc
find . -type f -name "*.pyc" -delete 2>/dev/null
```

## Ejemplos de Uso Correcto

### Ejemplo 1: En un servicio

```python
from src.config.settings import get_settings

class MyService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self.endpoint = settings.azure_doc_intelligence_endpoint
```

### Ejemplo 2: En un script

```python
from src.config.settings import get_settings

def main():
    settings = get_settings()

    print(f"Using model: {settings.claude_model}")
    print(f"Data dir: {settings.data_dir}")
```

### Ejemplo 3: Pasar configuración a funciones

```python
from src.config.settings import get_settings

def process_document(doc_path: str):
    settings = get_settings()

    # Usar la configuración
    model = settings.claude_model
    max_tokens = settings.claude_max_tokens

    # ... tu código aquí
```

## Verificación

Después de aplicar la solución, verifica que funcione:

```bash
# Desde la raíz del proyecto
python3 -c "from src.config.settings import get_settings; print('✅ Import correcto')"
```

Si ves "✅ Import correcto", el problema está resuelto.

## Prevención

**Regla de oro:** Nunca importes `settings` directamente. Siempre usa:

```python
from src.config.settings import get_settings

# Y luego:
settings = get_settings()
```

## ¿Necesitas Ayuda?

Si el problema persiste:

1. Asegúrate de haber limpiado todos los archivos compilados
2. Reinicia tu IDE/editor
3. Verifica que no haya archivos .py en `.gitignore` que puedan tener el error
4. Revisa que el archivo `.env` exista y tenga las variables requeridas
