"""
Endpoints para procesamiento de historias clínicas
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import logging
from pathlib import Path
from typing import Any, Dict
import json

from app.services.processor_service import ProcessorService
from app.services import empresa_service
from app.services.sve_service import evaluate_sve, canonicalize_sve_tokens, canonicalize_sve_id
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
        # Procesar documento y actualizar el archivo resultante
        result = processor_service.process_single_document(file)
        processing_id = result.get('id_procesamiento')
        if processing_id:
            output_path = processor_service.processed_folder / f"{processing_id}.json"
            try:
                with output_path.open('w', encoding='utf-8') as fh:
                    json.dump(result, fh, ensure_ascii=False, indent=2)
            except Exception:
                logger.exception("No se pudo actualizar el consolidado con alertas SVE: %s", output_path)

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
        empresa: Nombre de la empresa (requerido)
        documento: Documento del empleado (requerido)

    Returns:
        JSON con la historia clínica consolidada
    """
    # Validar que se enviaron archivos
    if 'files[]' not in request.files:
        return jsonify({'error': 'No se enviaron archivos'}), 400

    files = request.files.getlist('files[]')
    person_id = request.form.get('person_id')  # opcional (legacy)
    empresa_id = request.form.get('empresa_id', '').strip()
    empresa = request.form.get('empresa', '')
    documento = request.form.get('documento', '')
    ges_id = request.form.get('ges_id', '').strip()
    cargo = request.form.get('cargo', '').strip()

    if len(files) == 0:
        return jsonify({'error': 'Lista de archivos vacía'}), 400

    # Validar campos requeridos
    if not empresa_id:
        return jsonify({'error': 'El campo empresa_id es requerido'}), 400

    if not empresa or not empresa.strip():
        return jsonify({'error': 'El campo empresa es requerido'}), 400

    if not documento or not documento.strip():
        return jsonify({'error': 'El campo documento es requerido'}), 400

    # Validar cada archivo
    for file in files:
        if not allowed_file(file.filename):
            return jsonify({'error': 'Archivo no permitido: ' + str(file.filename)}), 400
        if not validate_file_size(file):
            return jsonify({'error': 'Archivo muy grande: ' + str(file.filename)}), 400

    try:
        # Procesar y consolidar documentos
        result = processor_service.process_person_documents(
            files,
            person_id,
            empresa_id=empresa_id,
            empresa=empresa.strip(),
            documento=documento.strip(),
            ges_id=ges_id or None,
            cargo=cargo or None
        )

        # Evaluar SVE con base en los diagnósticos consolidados
        diagnosticos_codes = [
            diag.get('codigo_cie10')
            for diag in (result.get('diagnosticos') or [])
            if diag.get('codigo_cie10')
        ]

        empresa_detalle = empresa_service.get_empresa(empresa_id)
        sve_entries = (empresa_detalle or {}).get('sve', []) if empresa_detalle else []

        empresa_sve_tokens: list[str] = []

        def register_token(token_source: Any) -> None:
            for token in canonicalize_sve_tokens(token_source):
                if token:
                    empresa_sve_tokens.append(token)
            canonical = canonicalize_sve_id(token_source)
            if canonical:
                empresa_sve_tokens.append(canonical)

        for entry in sve_entries:
            for key in ('sve_id', 'id', 'tipo', 'nombre'):
                register_token(entry.get(key))

        if not empresa_sve_tokens and empresa_detalle:
            for sve_id in empresa_detalle.get('sve_ids', []):
                register_token(sve_id)

        logger.info(
            "Evaluando SVE | empresa_id=%s tokens=%s diagnósticos=%s",
            empresa_id,
            empresa_sve_tokens,
            diagnosticos_codes,
        )
        sve_eval = evaluate_sve(diagnosticos_codes, empresa_sve_tokens)
        result['alertas_sve'] = sve_eval.get('alertas_sve', [])
        result['derivar_eps'] = sve_eval.get('derivar_eps', [])
        logger.info(
            "Resultado SVE | empresa_id=%s alertas=%s derivar_eps=%s",
            empresa_id,
            result['alertas_sve'],
            result['derivar_eps'],
        )

        processing_id = result.get('id_procesamiento')
        if processing_id:
            output_path = processor_service.processed_folder / f"{processing_id}.json"
            try:
                with output_path.open('w', encoding='utf-8') as fh:
                    json.dump(result, fh, ensure_ascii=False, indent=2)
            except Exception:
                logger.exception("No se pudo actualizar el consolidado con alertas SVE: %s", output_path)

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

        # Validar que result_ids sea una lista si se proporciona
        if result_ids and not isinstance(result_ids, list):
            return jsonify({'detail': 'result_ids debe ser una lista de IDs'}), 400

        excel_file = processor_service.export_to_excel(result_ids)

        # Verificar que el archivo existe y no está vacío
        if not excel_file.exists():
            logger.error(f"El archivo Excel no se generó correctamente: {excel_file}")
            return jsonify({'detail': 'Error: el archivo Excel no se generó correctamente'}), 500

        if excel_file.stat().st_size == 0:
            logger.error(f"El archivo Excel está vacío: {excel_file}")
            return jsonify({'detail': 'Error: el archivo Excel está vacío'}), 500

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='resultados_hc.xlsx'
        )
    except ValueError as e:
        logger.error(f"Error de validación al exportar a Excel: {str(e)}")
        return jsonify({'detail': str(e)}), 400
    except Exception as e:
        logger.exception("Error al exportar a Excel")
        return jsonify({'detail': f'Error al exportar a Excel: {str(e)}'}), 500


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
