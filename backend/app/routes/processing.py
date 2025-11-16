"""
Endpoints para procesamiento de historias clínicas
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import logging
from pathlib import Path

from app.services.processor_service import ProcessorService
from app.utils.validators import allowed_file, validate_file_size

logger = logging.getLogger(__name__)

bp = Blueprint('processing', __name__)
processor_service = ProcessorService()


@bp.route('/process', methods=['POST'])
def process_document():
    """
    Procesar un solo documento PDF

    Body (multipart/form-data):
        file: archivo PDF

    Returns:
        JSON con la historia clínica procesada
    """
    # Validar que se envió un archivo
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    # Validar tipo de archivo
    if not allowed_file(file.filename):
        return jsonify({'error': 'Solo se permiten archivos PDF'}), 400

    # Validar tamaño (ya está en Flask config, pero validamos explícitamente)
    if not validate_file_size(file):
        return jsonify({'error': 'El archivo excede el tamaño máximo de 10MB'}), 400

    try:
        # Procesar documento
        result = processor_service.process_single_document(file)
        return jsonify(result), 200

    except Exception:
        logger.exception("Error al procesar documento")
        return jsonify({'error': 'Error al procesar documento.'}), 500


@bp.route('/process-person', methods=['POST'])
def process_person():
    """
    Procesar múltiples documentos de una persona y consolidar

    Body (multipart/form-data):
        files[]: lista de archivos PDF
        person_id: ID de la persona (opcional)

    Returns:
        JSON con la historia clínica consolidada
    """
    # Validar que se enviaron archivos
    if 'files[]' not in request.files:
        return jsonify({'error': 'No se enviaron archivos'}), 400

    files = request.files.getlist('files[]')
    person_id = request.form.get('person_id', 'consolidated')

    if len(files) == 0:
        return jsonify({'error': 'Lista de archivos vacía'}), 400

    # Validar cada archivo
    for file in files:
        if not allowed_file(file.filename):
            return jsonify({'error': 'Archivo no permitido: ' + str(file.filename)}), 400
        if not validate_file_size(file):
            return jsonify({'error': 'Archivo muy grande: ' + str(file.filename)}), 400

    try:
        # Procesar y consolidar documentos
        result = processor_service.process_person_documents(files, person_id)
        return jsonify(result), 200

    except Exception:
        logger.exception("Error al procesar documentos")
        return jsonify({'error': 'Error al procesar documentos.'}), 500


@bp.route('/results', methods=['GET'])
def get_all_results():
    """
    Obtener lista de todos los resultados procesados

    Returns:
        Lista de JSONs procesados
    """
    try:
        results = processor_service.get_all_results()
        return jsonify(results), 200
    except Exception:
        logger.exception("Error al obtener resultados")
        return jsonify({'error': 'Error al obtener resultados.'}), 500


@bp.route('/results/<result_id>', methods=['GET'])
def get_result(result_id):
    """
    Obtener un resultado específico por ID

    Args:
        result_id: ID del procesamiento

    Returns:
        JSON del resultado procesado
    """
    try:
        result = processor_service.get_result_by_id(result_id)
        if result:
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Resultado no encontrado'}), 404
    except Exception:
        logger.exception("Error al obtener resultado")
        return jsonify({'error': 'Error al obtener resultado.'}), 500


@bp.route('/export/excel', methods=['POST'])
def export_to_excel():
    """
    Exportar resultados a Excel

    Body (JSON):
        result_ids: lista de IDs a exportar (opcional, si no se envía exporta todos)

    Returns:
        Archivo Excel
    """
    try:
        data = request.get_json()
        result_ids = data.get('result_ids', []) if data else []

        excel_file = processor_service.export_to_excel(result_ids)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='resultados_hc.xlsx'
        )
    except Exception:
        logger.exception("Error al exportar a Excel")
        return jsonify({'error': 'Error al exportar a Excel.'}), 500


@bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    Obtener estadísticas del procesamiento

    Returns:
        JSON con estadísticas
    """
    try:
        stats = processor_service.get_statistics()
        return jsonify(stats), 200
    except Exception:
        logger.exception("Error al obtener estadísticas")
        return jsonify({'error': 'Error al obtener estadísticas.'}), 500
