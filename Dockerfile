# Backend - Narah HC Processor
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt ./requirements.txt
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r backend/requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY backend/ ./backend/
COPY config/ ./config/

# Crear directorios necesarios
RUN mkdir -p data/raw data/processed data/labeled logs

# Variables de entorno por defecto
ENV FLASK_ENV=production
ENV FLASK_APP=app.py
ENV HOST=0.0.0.0
ENV PORT=5050
ENV LOG_LEVEL=INFO

EXPOSE 5050

# Ejecutar con gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "2", "--timeout", "600", "--chdir", "backend", "app:app"]
