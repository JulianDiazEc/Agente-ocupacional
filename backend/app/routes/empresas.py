from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services import empresa_service

empresas_bp = Blueprint("empresas", __name__)


@empresas_bp.route("/empresas", methods=["GET"])
def list_empresas():
    empresas = empresa_service.get_all_empresas()
    return jsonify(empresas), 200


@empresas_bp.route("/empresas/<empresa_id>", methods=["GET"])
def get_empresa(empresa_id: str):
    empresa = empresa_service.get_empresa(empresa_id)
    if not empresa:
        return jsonify({"error": "Empresa no encontrada"}), 404
    return jsonify(empresa), 200


@empresas_bp.route("/empresas", methods=["POST"])
def create_empresa():
    data = request.get_json() or {}
    try:
        empresa = empresa_service.create_empresa(data)
        return jsonify(empresa), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@empresas_bp.route("/empresas/<empresa_id>", methods=["PUT"])
def update_empresa(empresa_id: str):
    data = request.get_json() or {}
    empresa = empresa_service.update_empresa(empresa_id, data)
    if not empresa:
        return jsonify({"error": "Empresa no encontrada"}), 404
    return jsonify(empresa), 200


@empresas_bp.route("/empresas/<empresa_id>/ges", methods=["POST"])
def add_ges(empresa_id: str):
    data = request.get_json() or {}
    try:
        ges = empresa_service.add_ges(empresa_id, data)
        return jsonify(ges), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@empresas_bp.route("/empresas/<empresa_id>/ges/<ges_id>", methods=["PUT"])
def update_ges(empresa_id: str, ges_id: str):
    data = request.get_json() or {}
    updated = empresa_service.update_ges(empresa_id, ges_id, data)
    if not updated:
        return jsonify({"error": "GES no encontrado"}), 404
    return jsonify(updated), 200


@empresas_bp.route("/empresas/<empresa_id>/sve", methods=["POST"])
def add_sve(empresa_id: str):
    data = request.get_json() or {}
    try:
        sve = empresa_service.add_sve(empresa_id, data)
        return jsonify(sve), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@empresas_bp.route("/empresas/<empresa_id>/sve", methods=["PUT"])
def set_sve(empresa_id: str):
    data = request.get_json() or {}
    tipos = data.get("tipos") or []
    try:
        result = empresa_service.set_sve_list(empresa_id, tipos)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
