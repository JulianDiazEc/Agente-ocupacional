"""
Inicialización de la aplicación Flask
"""
from flask import Flask
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


def create_app():
    """Factory para crear la aplicación Flask"""

    app = Flask(__name__)

    # Cargar configuración
    config_class = get_config()
    print(f"DEBUG: config_class = {config_class}")
    print(f"DEBUG: config_class type = {type(config_class)}")
    print(f"DEBUG: hasattr CORS_ORIGINS = {hasattr(config_class, 'CORS_ORIGINS')}")
    
    app.config.from_object(config_class)
    
    # Debug: verificar que la configuración se cargó correctamente
    print(f"DEBUG: CORS_ORIGINS = {app.config.get('CORS_ORIGINS', 'NOT FOUND')}")
    print(f"DEBUG: Config keys = {list(app.config.keys())}")

    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
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

    # Registrar blueprints/routes
    from app.routes import processing, health
    from app.routes.empresas import empresas_bp  # 👈 NUEVA LÍNEA

    app.register_blueprint(processing.bp, url_prefix='/api')
    app.register_blueprint(health.bp, url_prefix='/api')
    app.register_blueprint(empresas_bp, url_prefix='/api')  # 👈 NUEVA LÍNEA

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