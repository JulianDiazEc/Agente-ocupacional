"""
Inicialización de la aplicación Flask
"""
from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sys
from pathlib import Path

# Añadir el directorio src/ al PYTHONPATH para importar módulos del CLI
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_config


def create_app():
    """Factory para crear la aplicación Flask"""

    app = Flask(__name__)

    # Cargar configuración
    config_class = get_config()
    app.config.from_object(config_class)

    # Inicializar extensiones
    CORS(app, origins=app.config['CORS_ORIGINS'])
    api = Api(app)

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[app.config['RATE_LIMIT']],
        storage_uri="memory://"
    )

    # Registrar blueprints/routes
    from app.routes import processing, health

    app.register_blueprint(processing.bp, url_prefix='/api')
    app.register_blueprint(health.bp, url_prefix='/api')

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
