"""
Health check endpoints
"""
from flask import Blueprint, jsonify
from datetime import datetime

bp = Blueprint('health', __name__)


@bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Narah HC Processor API',
        'version': '1.0.0'
    }), 200


@bp.route('/ping', methods=['GET'])
def ping():
    """Endpoint simple de ping"""
    return jsonify({'message': 'pong'}), 200
