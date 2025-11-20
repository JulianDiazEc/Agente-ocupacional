from flask import Blueprint, jsonify, request
import logging

from app.services.empresa_service import empresa_service

bp = Blueprint('empresa', __name__)
logger = logging.getLogger(__name__)


@bp.route('/empresas', methods=['GET'])
def list_empresas():
    empresas = empresa_service.get_all_empresas()
    return jsonify(empresas), 200


@bp.route('/empresas/<empresa_id>', methods=['GET'])
def get_empresa(empresa_id):
    empresa = empresa_service.get_empresa(empresa_id)
    if not empresa:
        return jsonify({'error': 'Empresa no encontrada'}), 404
    return jsonify(empresa), 200


@bp.route('/empresas', methods=['POST'])
def create_empresa():
    payload = request.get_json(force=True, silent=True) or {}
    try:
        empresa = empresa_service.create_empresa(payload)
        return jsonify(empresa), 201
    except ValueError as exc:
        logger.warning("Error creando empresa: %s", exc)
        return jsonify({'error': str(exc)}), 400


@bp.route('/empresas/<empresa_id>', methods=['PUT'])
def update_empresa(empresa_id):
    payload = request.get_json(force=True, silent=True) or {}
    try:
        empresa = empresa_service.update_empresa(empresa_id, payload)
        return jsonify(empresa), 200
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@bp.route('/empresas/<empresa_id>/ges', methods=['POST'])
def add_ges(empresa_id):
    payload = request.get_json(force=True, silent=True) or {}
    try:
        registro = empresa_service.add_ges(empresa_id, payload)
        return jsonify(registro), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@bp.route('/empresas/<empresa_id>/ges/<ges_id>', methods=['PUT'])
def update_ges(empresa_id, ges_id):
    payload = request.get_json(force=True, silent=True) or {}
    try:
        registro = empresa_service.update_ges(empresa_id, ges_id, payload)
        return jsonify(registro), 200
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@bp.route('/empresas/<empresa_id>/sve', methods=['POST'])
def add_sve(empresa_id):
    payload = request.get_json(force=True, silent=True) or {}
    try:
        registro = empresa_service.add_sve(empresa_id, payload)
        return jsonify(registro), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@bp.route('/empresas/<empresa_id>/sve', methods=['PUT'])
def set_sve(empresa_id):
    payload = request.get_json(force=True, silent=True) or {}
    tipos = payload.get('tipos') or []
    try:
        registros = empresa_service.set_sve_list(empresa_id, tipos)
        return jsonify(registros), 200
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
