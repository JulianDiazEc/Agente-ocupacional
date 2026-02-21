"""
Inicialización de la aplicación Flask
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restful import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sys
import logging
import os
from pathlib import Path

# Añadir el directorio backend primero para importar config
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Importar config desde el backend
from config import get_config

# Añadir el directorio src/ al PYTHONPATH para importar módulos del CLI
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))


# Rutas públicas que no requieren autenticación
PUBLIC_ROUTES = {'/api/health', '/api/ping'}


def create_app():
    """Factory para crear la aplicación Flask"""

    app = Flask(__name__)

    # Cargar configuración
    config_class = get_config()
    app.config.from_object(config_class)

    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )

    # Inicializar extensiones
    CORS(app, origins=app.config['CORS_ORIGINS'])
    api = Api(app)

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[app.config['RATE_LIMIT']],
        storage_uri="memory://"
    )

    # Middleware de autenticación por API Key
    @app.before_request
    def authenticate():
        """Valida X-API-Key header en rutas protegidas."""
        if request.path in PUBLIC_ROUTES:
            return None

        api_key = app.config.get('API_KEY')
        if not api_key:
            # Si no hay API_KEY configurada, permitir acceso (desarrollo)
            return None

        request_key = request.headers.get('X-API-Key')
        if not request_key or request_key != api_key:
            return jsonify({'error': 'API key inválida o faltante'}), 401

    # Registrar blueprints/routes
    from app.routes import processing, health
    from app.routes.empresas import empresas_bp

    app.register_blueprint(processing.bp, url_prefix='/api')
    app.register_blueprint(health.bp, url_prefix='/api')
    app.register_blueprint(empresas_bp, url_prefix='/api')

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Recurso no encontrado'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Error interno del servidor'}, 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return {'error': 'Archivo demasiado grande. Máximo 10MB'}, 413

    return app
