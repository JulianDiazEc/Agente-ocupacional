"""
Health check endpoints
"""
import os
import time
from flask import Blueprint, jsonify, current_app
from datetime import datetime

bp = Blueprint('health', __name__)

_start_time = time.time()


@bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check con detalles del sistema."""
    uptime_seconds = int(time.time() - _start_time)

    # Verificar servicios externos
    services = {}

    # Azure
    azure_endpoint = current_app.config.get('AZURE_DOC_INTELLIGENCE_ENDPOINT')
    azure_key = current_app.config.get('AZURE_DOC_INTELLIGENCE_KEY')
    services['azure'] = 'configured' if (azure_endpoint and azure_key) else 'not_configured'

    # Claude
    anthropic_key = current_app.config.get('ANTHROPIC_API_KEY')
    services['claude'] = 'configured' if anthropic_key else 'not_configured'

    # Auth
    api_key = current_app.config.get('API_KEY')
    services['auth'] = 'enabled' if api_key else 'disabled'

    # Costos del día
    daily_costs = None
    try:
        from src.utils.cost_tracker import get_cost_tracker
        tracker = get_cost_tracker()
        daily_costs = tracker.get_daily_summary()
    except Exception:
        pass

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Narah HC Processor API',
        'version': '1.0.0',
        'uptime_seconds': uptime_seconds,
        'environment': os.getenv('FLASK_ENV', 'development'),
        'services': services,
        'costs_today': daily_costs,
    }), 200


@bp.route('/ping', methods=['GET'])
def ping():
    """Endpoint simple de ping"""
    return jsonify({'message': 'pong'}), 200
