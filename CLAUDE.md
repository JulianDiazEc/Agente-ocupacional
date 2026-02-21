# CLAUDE.md - Narah HC Processor (Agente Ocupacional)

## Qué es este proyecto

Sistema de procesamiento de historias clínicas ocupacionales (SST) que transforma PDFs médicos no estructurados en datos JSON estructurados y validados. Usa Azure Document Intelligence para OCR y Claude API para extracción inteligente.

**Pipeline**: PDF → Azure OCR → Claude AI (extracción estructurada) → Validación → Enriquecimiento GES → Exportación (JSON/Excel/PDF)

## Tech Stack

- **Backend**: Python 3.10+, Flask, Pydantic v2
- **Frontend**: React 18, TypeScript 5.3, Vite 5, Material-UI v5
- **AI/ML**: Anthropic Claude API (Sonnet 4), Azure Document Intelligence (prebuilt-layout)
- **Testing**: pytest
- **Linting**: black, ruff, mypy

## Arquitectura del proyecto

```
src/
├── cli.py                          # CLI principal (click)
├── config/
│   ├── settings.py                 # Configuración (Pydantic BaseSettings, .env)
│   └── schemas.py                  # Modelos Pydantic (HistoriaClinicaEstructurada, Diagnostico, etc.)
├── extractors/
│   ├── base.py                     # Clase abstracta PDFExtractor
│   └── azure_extractor.py          # Azure Document Intelligence OCR
├── processors/
│   ├── claude_processor.py         # Orquestador principal LLM (extracción + dedup)
│   ├── prompts.py                  # Prompts de extracción médica
│   ├── validators.py               # Validación CIE-10, signos vitales, consistencia
│   ├── ges_enricher.py             # Enriquecimiento GES/SVE
│   ├── alert_filters.py            # Filtrado de alertas (whitelist)
│   └── recommendation_filters.py   # Filtrado de recomendaciones genéricas
├── exporters/
│   ├── json_exporter.py            # Exportación JSON
│   ├── excel_exporter.py           # Exportación Excel multi-hoja
│   └── pdf_exporter.py             # Exportación PDF (reportlab)
└── utils/
    ├── helpers.py                  # JSON parsing, normalización
    └── logger.py                   # Logging JSON con rotación

backend/
├── app.py                         # Flask app factory
├── config.py                      # Configuración Flask
└── app/
    ├── routes/
    │   ├── processing.py           # POST /process, POST /process-person
    │   ├── empresa.py              # Rutas de empresa
    │   └── health.py               # GET /health
    └── services/
        ├── processor_service.py    # Orquestación extracción + procesamiento
        ├── sve_service.py          # Evaluación SVE
        └── empresa_service.py      # Gestión de empresas

frontend/src/
├── pages/                          # HomePage, UploadPage, ResultsListPage, ResultDetailPage, ExportPage
├── components/                     # upload/, results/, alerts/, common/, layout/
├── services/                       # api.ts, processing.service.ts, export.service.ts
├── contexts/                       # ProcessingContext, ResultsContext, ThemeContext
├── types/medical.ts                # Interfaces TypeScript del dominio médico
└── theme/                          # Material-UI config (primary: #EC4899)
```

## Comandos frecuentes

```bash
# Backend
python src/cli.py process <archivo.pdf>              # Procesar un PDF
python src/cli.py batch <directorio>                  # Procesamiento batch
python -m pytest tests/                               # Tests
python -m pytest tests/ -v --tb=short                 # Tests verbose

# Frontend
cd frontend && npm run dev                            # Dev server
cd frontend && npm run build                          # Build producción

# Backend API
cd backend && python app.py                           # Servidor Flask
```

## Conceptos de dominio clave

- **EMO**: Examen Médico Ocupacional (preingreso, periódico, retiro, cambio de ocupación, post-incapacidad)
- **CIE-10**: Clasificación Internacional de Enfermedades. Formato: Letra + 2 dígitos + opcional (.1-2 dígitos). Ej: M54.5, H52.0
- **SVE**: Sistema de Vigilancia Epidemiológica. Programas: DME, Ruido, Biológico, Psicosocial, Cardiovascular, Visual, Respiratorio, BTX, Radiaciones, Voz
- **GES**: Grupo de Exposición Similar. Agrupa cargos con peligros similares dentro de una empresa
- **Aptitud laboral**: apto | apto_con_restricciones | no_apto_temporal | no_apto_definitivo
- **HC**: Historia Clínica
- **CMO**: Certificado Médico Ocupacional
- **Consolidado**: Fusión de múltiples documentos de una misma persona (HC + RX + Labs)

## Modelo de datos principal

`HistoriaClinicaEstructurada` (schemas.py) es el modelo central con:
- `datos_empleado`: Info personal y laboral
- `diagnosticos[]`: Lista con código CIE-10, descripción, tipo (principal/secundario), relación laboral
- `examenes[]`: Resultados de exámenes (audiometría, visiometría, espirometría, laboratorio, etc.)
- `signos_vitales`: PA, FC, SpO2, peso, talla, IMC
- `antecedentes[]`: Personales, familiares, laborales
- `aptitud_laboral`: Concepto de aptitud del médico
- `recomendaciones[]`: Recomendaciones médicas y ocupacionales
- `programas_sve[]`: Programas de vigilancia epidemiológica aplicables
- `alertas_validacion[]`: Alertas generadas por el sistema (severidad: critica, alta, media, baja)
- `confianza_extraccion`: Score 0-1 de confianza

## Reglas de negocio importantes

- Los diagnósticos NO deben incluir nombres de exámenes (audiometría, visiometría) ni hallazgos normales como diagnósticos
- La deduplicación de diagnósticos usa matching exacto + fuzzy similarity
- Las alertas usan enfoque whitelist: siempre mantener críticas/formato/inconsistencia, filtrar ruido administrativo
- Los códigos CIE-10 se validan por formato regex Y por rango de capítulo válido
- El prompt caching reduce costos ~78% ($3 → $0.66 por 40 HCs)
- Temperature del modelo: 0.0 (determinístico)
- Max tokens: 8000

## Servicios externos

- **Azure Document Intelligence**: OCR con modelo `prebuilt-layout`. Retry con backoff exponencial (3 intentos)
- **Anthropic Claude API**: Modelo por defecto `claude-sonnet-4-20250514`. Prompt caching habilitado (TTL 3600s)

## Variables de entorno requeridas (.env)

```
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://...cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=<key>
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
ENABLE_PROMPT_CACHING=true
LOG_LEVEL=INFO
```

## Configuración empresarial

- `config/empresas/data.json`: Define empresas, GES (grupos de exposición), cargos, peligros, exámenes requeridos
- `config/empresas/sve_catalog.json`: Catálogo de programas SVE
- Cada GES mapea cargos → peligros → exámenes → programas SVE → criterios clínicos

## Directorios de datos

```
data/raw/        # PDFs de entrada
data/processed/  # JSONs de salida
data/labeled/    # Ground truth para validación
```

## Convenciones de código

- **Python**: PEP 8, type hints en funciones públicas, Pydantic para modelos de datos
- **Frontend**: TypeScript strict, componentes funcionales con hooks, Material-UI
- **Commits**: Mensajes descriptivos en español o inglés
- **Normativa colombiana**: Resolución 1843/2021 para lenguaje de aptitud laboral
