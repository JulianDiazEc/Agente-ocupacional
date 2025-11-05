# Narah HC Processor

Sistema profesional de procesamiento automatizado de historias clínicas ocupacionales para **Narah Metrics 2.0**.

Transforma PDFs de historias clínicas (nativos o escaneados) en datos estructurados JSON mediante Azure Document Intelligence y Claude API (Anthropic).

---

## 🎯 Características Principales

- ✅ **Extracción de PDFs**: Soporte para documentos nativos y escaneados (OCR) con Azure Document Intelligence
- ✅ **Procesamiento Inteligente**: Estructuración de datos médicos con Claude Sonnet 4
- ✅ **Validación Robusta**: Validación automática de CIE-10, fechas, y valores clínicos
- ✅ **Alertas Médicas**: Detección automática de inconsistencias y valores críticos
- ✅ **Export Flexible**: JSON estructurado y Excel para análisis
- ✅ **CLI Intuitivo**: Interfaz de línea de comandos con Rich (colores y progress bars)
- ✅ **Batch Processing**: Procesamiento paralelo de múltiples historias clínicas
- ✅ **Análisis de Calidad**: Script estadístico para evaluar calidad del procesamiento batch
- ✅ **Validación Manual**: Herramienta interactiva para crear ground truth y validar campos

---

## 📋 Requisitos Previos

### 1. Python 3.10+

```bash
python --version  # Debe ser >= 3.10
```

### 2. Credenciales Azure Document Intelligence

Necesitas crear un recurso de **Azure Document Intelligence** (antes Form Recognizer):

1. Ve a [Azure Portal](https://portal.azure.com)
2. Crea un recurso de "Document Intelligence" o "Form Recognizer"
3. Copia el **Endpoint** y una **API Key** desde "Keys and Endpoint"

### 3. API Key de Anthropic Claude

1. Ve a [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Genera una API Key
3. Asegúrate de tener créditos disponibles

---

## 🚀 Instalación

### Paso 1: Clonar el repositorio

```bash
git clone <repository-url>
cd narah-hc-processor
```

### Paso 2: Crear entorno virtual

```bash
python -m venv venv

# Activar en Linux/Mac
source venv/bin/activate

# Activar en Windows
venv\Scripts\activate
```

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Configurar variables de entorno

```bash
# Copiar el template
cp .env.example .env

# Editar .env con tus credenciales
nano .env  # o usa tu editor favorito
```

**Configuración mínima requerida en `.env`:**

```env
# Azure Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=your_32_character_key_here

# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Opcional: Configuración
LOG_LEVEL=INFO
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### Paso 5: Verificar instalación

```bash
python -m src.cli --version
```

Deberías ver: `cli, version 1.0.0`

---

## 📖 Guía de Uso

### Comandos Disponibles

```bash
python -m src.cli --help
```

#### 1. Procesar una HC individual

```bash
python -m src.cli process data/raw/HC_001.pdf
```

**Opciones:**

- `--output`, `-o`: Directorio de salida (default: `data/processed/`)
- `--show-result`, `-s`: Mostrar resumen del resultado en consola
- `--save-extraction`: Guardar texto extraído por Azure (útil para debugging)

**Ejemplo completo:**

```bash
python -m src.cli process data/raw/HC_123.pdf \
  --output ./output \
  --show-result \
  --save-extraction
```

**Output:**

- `output/HC_123.json`: Historia clínica estructurada
- `output/HC_123_extraction.txt`: Texto extraído (si se usa `--save-extraction`)

---

#### 2. Procesar múltiples HCs en batch

```bash
python -m src.cli batch data/raw/
```

**Opciones:**

- `--output`, `-o`: Directorio de salida
- `--workers`, `-w`: Número de workers paralelos (default: 5)
- `--pattern`, `-p`: Patrón de archivos (default: `*.pdf`)

**Ejemplo:**

```bash
python -m src.cli batch data/raw/ \
  --output data/processed/ \
  --workers 10 \
  --pattern "HC_*.pdf"
```

**Nota:** El procesamiento es secuencial (no paralelo real) debido a límites de rate de APIs.

---

#### 3. Ver resumen de HC procesada

```bash
python -m src.cli show data/processed/HC_001.json
```

**Muestra:**

- Datos del empleado
- Tipo y fecha del EMO
- Aptitud laboral y restricciones
- Diagnósticos (CIE-10)
- Exámenes realizados
- Programas SVE recomendados
- Alertas de validación

---

#### 4. Exportar a formato Narah Metrics

```bash
python -m src.cli export-narah data/processed/ --output narah_import.xlsx
```

**Genera un Excel con:**

- Hoja "Resumen": Datos generales de todos los empleados
- Hoja "Diagnósticos": Todos los diagnósticos con CIE-10
- Hoja "Exámenes": Resultados de exámenes paraclínicos
- Hoja "Recomendaciones": Recomendaciones médicas y ocupacionales
- Hoja "Alertas": Alertas de validación detectadas

---

#### 5. Analizar calidad del batch procesado

**Nuevo:** Script de análisis estadístico para evaluar la calidad del procesamiento batch.

```bash
# Análisis básico (muestra en terminal)
python analyze_batch.py

# Análisis con export a Excel
python analyze_batch.py --export estadisticas.xlsx

# Analizar directorio personalizado
python analyze_batch.py --dir ./custom_dir --export report.xlsx
```

**El análisis incluye:**

- **Métricas generales**: Total de HCs, confianza promedio/mín/máx
- **Alertas de validación**:
  - Total por severidad (alta/media/baja)
  - Top 5 tipos de alertas más comunes
  - HCs con/sin alertas
- **Campos con baja confianza**: Top 10 campos más afectados
- **Tipos de EMO**: Distribución (preingreso, periódico, etc.)
- **Diagnósticos CIE-10**:
  - Top 10 más frecuentes
  - Total y promedio por HC
  - Relacionados con trabajo
- **Aptitud laboral**: Distribución (apto, con restricciones, etc.)
- **Programas SVE**: Top 5 programas más asignados
- **Exámenes paraclínicos**: Distribución por tipo

**Output en terminal:**

El script usa Rich para mostrar tablas formateadas con colores en la terminal.

**Export a Excel:**

Genera archivo con 7 hojas:
1. Resumen
2. Confianza
3. Alertas
4. Diagnósticos
5. Aptitud
6. Programas SVE
7. Exámenes

**Ejemplo de uso típico:**

```bash
# 1. Procesar batch de HCs
python -m src.cli batch data/raw/ --workers 5

# 2. Analizar calidad del procesamiento
python analyze_batch.py --export analisis_calidad.xlsx

# 3. Revisar estadísticas y ajustar si es necesario
```

---

#### 6. Validar y crear ground truth

**Nuevo:** Herramienta interactiva para validar manualmente historias clínicas y crear ground truth de alta calidad.

```bash
# Validar una HC procesada
python validate_ground_truth.py data/raw/HC_001.pdf data/processed/HC_001.json

# Con directorio de salida personalizado
python validate_ground_truth.py HC_001.pdf HC_001.json --output data/labeled/
```

**Funcionalidad:**

El validador muestra **cada campo del JSON** junto con el **contexto del PDF original**, permitiendo:

- **[C]orrecto**: Marcar campo como válido
- **[E]ditar**: Corregir el valor manualmente
- **[S]altar**: Revisar más tarde
- **[Q]uit**: Guardar progreso y salir

**Interfaz interactiva:**

- ✅ UI con Rich (colores, tablas, paneles)
- ✅ Navegación simple con teclas
- ✅ Progress tracking (campo X de Y)
- ✅ Resalta campos con baja confianza en amarillo
- ✅ Campos con alertas en rojo
- ✅ Muestra contexto del PDF relevante

**Campos validados (orden de prioridad):**

1. Datos del empleado (nombre, documento, cargo, empresa)
2. Tipo y fecha de EMO
3. Aptitud laboral y restricciones
4. Diagnósticos (CIE-10, descripción) - Top 3
5. Exámenes (resultados, hallazgos) - Top 3
6. Recomendaciones - Top 2

**Output generado:**

```
data/labeled/
├── HC_001.json                      # JSON validado (ground truth)
└── HC_001_validation_report.txt    # Reporte detallado
```

**Reporte incluye:**

- Estadísticas de validación
- Precisión del sistema (% campos correctos)
- Lista de todas las correcciones realizadas
- Campos con baja confianza original
- Alertas de validación original

**Ejemplo de uso:**

```bash
# 1. Procesar HC
python -m src.cli process data/raw/HC_001.pdf

# 2. Validar manualmente
python validate_ground_truth.py data/raw/HC_001.pdf data/processed/HC_001.json

# Durante la validación:
# - Revisa cada campo uno por uno
# - Marca correctos o edita los incorrectos
# - El progreso se guarda automáticamente

# 3. Usar ground truth para evaluación
# Ahora tienes data/labeled/HC_001.json validado manualmente
```

**Casos de uso:**

- **Crear dataset de evaluación**: Validar 10-20 HCs para medir precisión real
- **Identificar errores sistemáticos**: Ver qué campos se corrigen más frecuentemente
- **Mejorar prompts**: Usar correcciones para ajustar el prompt de Claude
- **Auditoría de calidad**: Revisar HCs críticas manualmente

---

## 📊 Estructura de Datos (Schema)

El sistema genera JSONs con la siguiente estructura:

```json
{
  "id_procesamiento": "uuid-generado",
  "fecha_procesamiento": "2024-03-15T10:30:00",
  "archivo_origen": "HC_001.pdf",

  "datos_empleado": {
    "nombre_completo": "JUAN PÉREZ",
    "documento": "12345678",
    "tipo_documento": "CC",
    "cargo": "Operario de producción",
    "empresa": "EMPRESA XYZ S.A.S"
  },

  "tipo_emo": "periodico",
  "fecha_emo": "2024-03-10",

  "diagnosticos": [
    {
      "codigo_cie10": "M54.5",
      "descripcion": "Dolor lumbar bajo",
      "tipo": "principal",
      "relacionado_trabajo": true,
      "confianza": 0.95
    }
  ],

  "examenes": [
    {
      "tipo": "laboratorio",
      "nombre": "Hemograma completo",
      "resultado": "Normal",
      "interpretacion": "normal"
    }
  ],

  "aptitud_laboral": "apto_con_restricciones",
  "restricciones_especificas": "No levantar cargas mayores a 15kg",

  "programas_sve": ["dme"],

  "confianza_extraccion": 0.92,

  "alertas_validacion": [
    {
      "tipo": "inconsistencia_diagnostica",
      "severidad": "media",
      "campo_afectado": "diagnosticos",
      "descripcion": "Diagnóstico sin soporte en exámenes",
      "accion_sugerida": "Verificar con médico evaluador"
    }
  ]
}
```

**Schema completo:** Ver `config/schemas/output_schema.json`

**Modelo Pydantic:** Ver `src/config/schemas.py`

---

## 🔍 Validaciones Implementadas

El sistema valida automáticamente:

### 1. Códigos CIE-10

- ✅ Formato: `A00.0` (Letra + 2 dígitos + punto + 1 dígito)
- ✅ Rangos válidos por capítulo (A-Z)
- ✅ Alerta si formato es incorrecto

### 2. Fechas

- ✅ Formato ISO: `YYYY-MM-DD`
- ✅ Rango razonable (últimos 5 años para EMOs)
- ✅ No fechas futuras

### 3. Valores Clínicos Críticos

- ⚠️ Presión arterial ≥ 180/110 (crisis hipertensiva)
- ⚠️ Glicemia ≥ 200 mg/dL
- ⚠️ IMC < 16 o > 40
- ⚠️ Saturación de oxígeno < 90%

### 4. Consistencia de Datos

- ❌ Diagnóstico sin código CIE-10
- ❌ Aptitud laboral no definida
- ❌ Restricciones sin diagnósticos que las justifiquen
- ❌ Diagnóstico mencionado pero sin soporte en exámenes

---

## 🛠️ Troubleshooting

### Error: "Azure Document Intelligence credentials no configuradas"

**Solución:**

1. Verifica que el archivo `.env` existe
2. Verifica que `AZURE_DOC_INTELLIGENCE_ENDPOINT` y `AZURE_DOC_INTELLIGENCE_KEY` están configurados
3. El endpoint debe empezar con `https://`

### Error: "Anthropic API key inválida"

**Solución:**

1. Verifica que `ANTHROPIC_API_KEY` está en `.env`
2. La key debe empezar con `sk-ant-`
3. Verifica que tienes créditos en tu cuenta de Anthropic

### Error: "No se pudo parsear respuesta de Claude"

**Posibles causas:**

1. El texto extraído por Azure está muy corrupto
2. El PDF tiene formato muy atípico
3. Claude no pudo generar JSON válido

**Solución:**

1. Usa `--save-extraction` para ver el texto extraído
2. Verifica la calidad del PDF original
3. Revisa los logs en `logs/`

### PDFs escaneados no se procesan bien

**Solución:**

1. Azure Document Intelligence requiere PDFs con buena calidad de escaneo
2. Resolución mínima recomendada: 300 DPI
3. Asegúrate de que el texto sea legible

### Rate limit de APIs

**Claude API:**

- Free tier: ~5 requests/minuto
- Paid tier: Varía según plan

**Azure:**

- Free tier: 500 páginas/mes
- Paid tier: Ilimitado con cuota

**Solución:** Usa `--workers 1` para procesamiento más lento pero seguro.

---

## 📁 Estructura del Proyecto

```
narah-hc-processor/
├── README.md                    # Este archivo
├── requirements.txt             # Dependencias Python
├── pyproject.toml              # Configuración del proyecto
├── .env.example                # Template de variables de entorno
├── .gitignore
├── analyze_batch.py            # Script de análisis estadístico de batch
├── validate_ground_truth.py    # Herramienta de validación manual
│
├── src/
│   ├── cli.py                   # CLI principal
│   │
│   ├── config/
│   │   ├── settings.py          # Configuración global
│   │   └── schemas.py           # Schemas Pydantic
│   │
│   ├── extractors/
│   │   ├── base.py              # Interface base
│   │   └── azure_extractor.py   # Extractor con Azure
│   │
│   ├── processors/
│   │   ├── prompts.py           # Prompts para Claude
│   │   ├── validators.py        # Validadores
│   │   └── claude_processor.py  # Procesador principal
│   │
│   ├── exporters/
│   │   ├── json_exporter.py     # Export a JSON
│   │   └── excel_exporter.py    # Export a Excel
│   │
│   └── utils/
│       ├── logger.py            # Sistema de logging
│       └── helpers.py           # Funciones auxiliares
│
├── config/
│   ├── prompts/
│   │   └── extraction_prompt.txt  # Prompt maestro
│   └── schemas/
│       └── output_schema.json     # JSON Schema
│
├── data/                        # Gitignored (contiene PHI)
│   ├── raw/                     # PDFs originales
│   ├── processed/               # JSONs procesados
│   └── labeled/                 # Ground truth (evaluación)
│
└── tests/
    ├── test_validators.py
    └── test_helpers.py
```

---

## 🧪 Tests

Ejecutar tests:

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=src

# Verbose
pytest -v

# Un archivo específico
pytest tests/test_validators.py
```

---

## 🔐 Seguridad y Privacidad

**⚠️ IMPORTANTE: Este sistema procesa información médica protegida (PHI)**

### Recomendaciones:

1. **Nunca** commitear archivos `.env` con credenciales
2. **Nunca** commitear PDFs o JSONs con datos de pacientes
3. Los directorios `data/raw/`, `data/processed/`, y `data/labeled/` están en `.gitignore`
4. Asegúrate de cumplir con regulaciones locales (HIPAA, GDPR, Ley 1581 Colombia)
5. Usa Azure y Anthropic con sus configuraciones de privacidad habilitadas

### Cumplimiento Colombia:

- ✅ Ley 1581 de 2012 (Protección de Datos Personales)
- ✅ Resolución 2346 de 2007 (EMO en Colombia)
- ✅ No almacena datos sensibles sin consentimiento

---

## 📈 Roadmap

Futuras mejoras planeadas:

- [ ] Soporte para múltiples idiomas
- [ ] Detección automática de tipo de EMO
- [ ] Integración directa con API de Narah Metrics
- [ ] Dashboard web para visualización
- [ ] Exportación a FHIR (Fast Healthcare Interoperability Resources)
- [ ] Reconocimiento de firmas médicas
- [ ] Validación contra catálogo oficial CIE-10

---

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit tus cambios: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

---

## 📄 Licencia

Propietario - Narah Metrics © 2024

---

## 📞 Soporte

Para soporte técnico:

- Email: dev@narahmetrics.com
- Documentación completa en el código fuente

---

## ✨ Créditos

Desarrollado para **Narah Metrics 2.0**

**Stack Tecnológico:**

- [Azure Document Intelligence](https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence)
- [Anthropic Claude API](https://www.anthropic.com/api)
- [Pydantic](https://docs.pydantic.dev/)
- [Click](https://click.palletsprojects.com/)
- [Rich](https://rich.readthedocs.io/)

---

**¡Listo para procesar historias clínicas! 🚀**
