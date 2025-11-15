# Narah HC Processor - Backend API

API REST en Flask para procesamiento de historias clínicas ocupacionales.

## 🚀 Inicio Rápido

### Instalación

```bash
cd backend
python -m venv venv

# Activar entorno virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### Configuración

1. Copiar archivo de variables de entorno:
```bash
cp .env.example .env
```

2. Editar `.env` con tus credenciales de Azure y Anthropic (las mismas del proyecto principal)

### Desarrollo

```bash
python app.py
```

La API estará disponible en: `http://localhost:5000`

## 📡 Endpoints

### Health Check
- `GET /api/health` - Health check del servicio
- `GET /api/ping` - Ping simple

### Procesamiento
- `POST /api/process` - Procesar 1 PDF
- `POST /api/process-person` - Procesar múltiples PDFs (consolidado)
- `GET /api/results` - Listar todos los resultados
- `GET /api/results/<id>` - Obtener resultado específico

### Exportación
- `POST /api/export/excel` - Exportar a Excel
- `GET /api/stats` - Estadísticas del procesamiento

## 📁 Estructura

```
backend/
├── app.py              # Punto de entrada
├── config.py           # Configuración
├── requirements.txt    # Dependencias
├── app/
│   ├── __init__.py     # Factory de Flask
│   ├── routes/         # Blueprints (endpoints)
│   ├── services/       # Lógica de negocio
│   ├── models/         # Modelos de datos
│   ├── utils/          # Helpers
│   └── middleware/     # Middleware
├── uploads/            # PDFs temporales
└── processed/          # JSONs procesados
```

## 🔗 Integración con CLI Existente

El backend utiliza los módulos existentes en `src/`:
- `src.extractors.azure_extractor` - Extracción con Azure
- `src.processors.claude_processor` - Procesamiento con Claude
- `src.exporters.excel_exporter` - Exportación a Excel
- `src.config.settings` - Configuración compartida

## 🛠️ Tecnologías

- Flask 3.0
- Flask-CORS
- Flask-RESTful
- Marshmallow (serialización)
- Werkzeug (file handling)
- Gunicorn (producción)

## 🔒 Seguridad

- CORS configurado para frontend
- Validación de tipos de archivo (solo PDF)
- Límite de tamaño de archivo (10MB)
- Rate limiting (10 req/min)
- Sanitización de nombres de archivos
