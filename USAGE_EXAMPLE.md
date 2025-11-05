# Ejemplos de Uso - Narah HC Processor

Este documento muestra ejemplos prácticos de uso del sistema completo.

## 📝 Flujo de Trabajo Completo

### 1. Procesamiento Individual

Procesar una historia clínica y ver los resultados:

```bash
# Procesar HC con visualización de resultados
python -m src.cli process data/raw/HC_001.pdf --show-result

# Guardar también el texto extraído (para debugging)
python -m src.cli process data/raw/HC_001.pdf \
  --show-result \
  --save-extraction \
  --output data/processed/
```

### 2. Procesamiento en Batch

Procesar múltiples historias clínicas:

```bash
# Procesar todas las HCs de un directorio
python -m src.cli batch data/raw/

# Con configuración personalizada
python -m src.cli batch data/raw/ \
  --output data/processed/ \
  --workers 5 \
  --pattern "*.pdf"
```

### 3. Análisis de Calidad

Después de procesar un batch, analizar la calidad:

```bash
# Ver estadísticas en terminal
python analyze_batch.py

# Exportar a Excel para análisis detallado
python analyze_batch.py --export analisis_$(date +%Y%m%d).xlsx

# Analizar directorio personalizado
python analyze_batch.py \
  --dir data/processed/ \
  --export reportes/analisis_calidad.xlsx
```

### 4. Visualización de Resultados

```bash
# Ver resumen de una HC específica
python -m src.cli show data/processed/HC_001.json

# Ver resumen de múltiples HCs
for file in data/processed/*.json; do
  echo "=== $file ==="
  python -m src.cli show "$file"
  echo ""
done
```

### 5. Exportación a Narah Metrics

```bash
# Exportar todo el batch procesado
python -m src.cli export-narah data/processed/ \
  --output narah_import_$(date +%Y%m%d).xlsx
```

---

## 🎯 Casos de Uso Comunes

### Caso 1: Procesamiento Inicial de HCs

**Escenario:** Tienes 100 HCs nuevas en PDFs que necesitas digitalizar.

```bash
# 1. Colocar PDFs en data/raw/
cp /path/to/pdfs/*.pdf data/raw/

# 2. Procesar en batch
python -m src.cli batch data/raw/ --workers 5

# 3. Analizar calidad
python analyze_batch.py --export analisis_inicial.xlsx

# 4. Revisar alertas en Excel
# Abrir analisis_inicial.xlsx y revisar hoja "Alertas"

# 5. Si hay HCs con baja confianza, reprocesarlas manualmente
python -m src.cli process data/raw/HC_PROBLEMA.pdf --show-result --save-extraction
```

### Caso 2: Validación de Calidad de Extracción

**Escenario:** Verificar que los diagnósticos CIE-10 se están extrayendo correctamente.

```bash
# 1. Procesar batch
python -m src.cli batch data/raw/

# 2. Generar estadísticas
python analyze_batch.py --export validacion.xlsx

# 3. Revisar en terminal las alertas de tipo "formato_incorrecto"
python analyze_batch.py | grep "formato_incorrecto"

# 4. Ver diagnósticos más comunes
python analyze_batch.py | grep -A 10 "DIAGNÓSTICOS"
```

### Caso 3: Monitoreo de Procesamiento Continuo

**Escenario:** Procesas HCs diariamente y quieres mantener métricas de calidad.

```bash
#!/bin/bash
# Script: process_daily.sh

DATE=$(date +%Y%m%d)

# Procesar nuevas HCs del día
python -m src.cli batch data/raw/daily_$DATE/ \
  --output data/processed/daily_$DATE/

# Generar reporte de calidad
python analyze_batch.py \
  --dir data/processed/daily_$DATE/ \
  --export reportes/calidad_$DATE.xlsx

# Enviar notificación
echo "Procesadas $(ls data/processed/daily_$DATE/*.json | wc -l) HCs el $DATE" | \
  mail -s "Reporte Diario HC Processor" admin@narahmetrics.com
```

### Caso 4: Depuración de HC Problemática

**Escenario:** Una HC no se procesa correctamente y muestra errores.

```bash
# 1. Procesar con máximo detalle
python -m src.cli process data/raw/HC_PROBLEMA.pdf \
  --save-extraction \
  --output debug/

# 2. Revisar el texto extraído
cat debug/HC_PROBLEMA_extraction.txt

# 3. Revisar el JSON generado
python -m src.cli show debug/HC_PROBLEMA.json

# 4. Verificar logs
tail -f logs/src_processors_claude_processor.log
```

### Caso 5: Análisis de Tendencias de Diagnósticos

**Escenario:** Identificar los diagnósticos ocupacionales más comunes.

```bash
# Generar estadísticas completas
python analyze_batch.py --export tendencias.xlsx

# Abrir Excel y revisar:
# - Hoja "Diagnósticos": Top 10 CIE-10 más comunes
# - Hoja "Programas SVE": Qué programas se asignan más
# - Hoja "Aptitud": Distribución de aptitudes laborales
```

---

## 🔍 Interpretación de Resultados

### Métricas de Confianza

```
Confianza promedio: 92%
✅ EXCELENTE: >90% - Procesamiento de alta calidad
⚠️  ACEPTABLE: 70-90% - Revisar campos con baja confianza
❌ BAJA: <70% - Requiere revisión manual
```

### Alertas por Severidad

```
Alta (roja):    Requiere atención inmediata
                Ejemplos: CIE-10 inválido, aptitud faltante

Media (amarilla): Revisar cuando sea posible
                  Ejemplos: Diagnóstico sin soporte en exámenes

Baja (blanca):  Informativa
                Ejemplos: Campo con confianza <0.7
```

### Campos con Baja Confianza

Si un campo aparece frecuentemente:
1. Verificar la calidad de los PDFs originales
2. Ajustar el prompt en `src/processors/prompts.py`
3. Considerar validación manual para ese campo

---

## 📊 Análisis Avanzado con Python

Puedes usar las clases del proyecto para análisis personalizado:

```python
# analisis_personalizado.py
from pathlib import Path
from src.exporters.json_exporter import load_historia_from_json

# Cargar todas las HCs
historias = []
for json_file in Path("data/processed").glob("*.json"):
    hist = load_historia_from_json(json_file)
    historias.append(hist)

# Análisis personalizado: HCs con restricciones laborales
hcs_con_restricciones = [
    h for h in historias
    if h.restricciones_especificas is not None
]

print(f"Total HCs con restricciones: {len(hcs_con_restricciones)}")

for h in hcs_con_restricciones:
    print(f"\n{h.datos_empleado.nombre_completo}:")
    print(f"  Aptitud: {h.aptitud_laboral}")
    print(f"  Restricciones: {h.restricciones_especificas}")
    print(f"  Diagnósticos:")
    for d in h.diagnosticos:
        print(f"    - {d.codigo_cie10}: {d.descripcion}")
```

---

## 🚀 Tips y Mejores Prácticas

### 1. Organización de Archivos

```
data/
├── raw/
│   ├── 2024_01/          # Organizar por mes
│   ├── 2024_02/
│   └── 2024_03/
├── processed/
│   ├── 2024_01/
│   ├── 2024_02/
│   └── 2024_03/
└── reportes/
    ├── analisis_2024_01.xlsx
    ├── analisis_2024_02.xlsx
    └── analisis_2024_03.xlsx
```

### 2. Backup de Datos Procesados

```bash
# Backup diario
tar -czf backups/processed_$(date +%Y%m%d).tar.gz data/processed/

# Backup con rotación (mantener últimos 30 días)
find backups/ -name "processed_*.tar.gz" -mtime +30 -delete
```

### 3. Monitoreo de Logs

```bash
# Ver logs en tiempo real
tail -f logs/*.log

# Buscar errores
grep -i error logs/*.log

# Contar procesamiento exitosos vs errores
grep "Procesamiento exitoso" logs/src_processors_claude_processor.log | wc -l
grep "Error procesando" logs/src_processors_claude_processor.log | wc -l
```

### 4. Optimización de Rate Limits

```bash
# Si tienes rate limits estrictos, procesar de a pocos
for pdf in data/raw/*.pdf; do
  python -m src.cli process "$pdf"
  sleep 15  # Esperar 15 segundos entre cada uno
done
```

---

## 📞 Soporte

Si encuentras problemas, revisa:

1. **Logs**: `logs/` - Detalles de errores
2. **Texto extraído**: Usa `--save-extraction` para ver qué vio Azure
3. **README.md**: Sección de Troubleshooting
4. **analyze_batch.py**: Métricas de calidad del batch

Para reportar bugs o solicitar features:
- Email: dev@narahmetrics.com
- GitHub Issues: [Crear issue](https://github.com/tu-repo/issues)
