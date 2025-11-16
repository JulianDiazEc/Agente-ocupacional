"""
Servicio para procesamiento de historias clínicas
Integra con los módulos existentes en src/
"""
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter
import logging

# Importar módulos del CLI existente
from src.extractors.azure_extractor import AzureDocumentExtractor
from src.processors.claude_processor import ClaudeProcessor, validate_signos_vitales, normalize_aptitud_laboral
from src.exporters.excel_exporter import ExcelExporter
from src.config.schemas import HistoriaClinicaEstructurada
from src.processors.validators import (
    validate_historia_completa,
    validate_diagnosis_exam_consistency,
    validate_examenes_criticos_sin_reflejo
)
from src.processors.alert_filters import filter_alerts

logger = logging.getLogger(__name__)


class ProcessorService:
    """Servicio de procesamiento de HCs"""

    def __init__(self):
        # Usar la configuración de Flask para obtener las rutas
        from config import get_config
        config = get_config()

        self.upload_folder = Path(config.UPLOAD_FOLDER)
        self.processed_folder = Path(config.PROCESSED_FOLDER)

        # Log de las rutas para debugging
        logger.info(f"ProcessorService inicializado")
        logger.info(f"  upload_folder: {self.upload_folder.absolute()}")
        logger.info(f"  processed_folder: {self.processed_folder.absolute()}")

        # Asegurar que las carpetas existen
        self.upload_folder.mkdir(exist_ok=True, parents=True)
        self.processed_folder.mkdir(exist_ok=True, parents=True)

        # Inicializar procesadores (del CLI existente)
        self.extractor = AzureDocumentExtractor()
        self.processor = ClaudeProcessor()

    def process_single_document(self, file: FileStorage, save: bool = True) -> Dict[str, Any]:
        """
        Procesar un solo documento PDF

        Args:
            file: Archivo PDF cargado
            save: Si True, guarda el resultado en disco. Si False, solo lo retorna (útil para consolidación)

        Returns:
            JSON con la HC procesada
        """
        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        temp_filename = f"{file_id}_{filename}"
        temp_path = self.upload_folder / temp_filename

        file.save(str(temp_path))

        try:
            # 1. Extraer texto con Azure
            extracted_text = self.extractor.extract(temp_path)

            # 2. Procesar con Claude (retorna objeto Pydantic)
            historia_pydantic = self.processor.process(extracted_text, filename)

            # 3. Convertir a diccionario JSON serializable
            processed_data = historia_pydantic.model_dump(mode='json')

            # 4. Guardar resultado solo si save=True
            if save:
                # Guardar usando el id_procesamiento del JSON (para que coincida al buscar luego)
                processing_id = processed_data.get('id_procesamiento', file_id)
                result_filename = f"{processing_id}.json"
                result_path = self.processed_folder / result_filename

                with open(result_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, ensure_ascii=False, indent=2)

            return processed_data

        finally:
            # Limpiar archivo temporal
            if temp_path.exists():
                temp_path.unlink()

    def process_person_documents(
        self,
        files: List[FileStorage],
        person_id: str,
        empresa: str = None,
        documento: str = None
    ) -> Dict[str, Any]:
        """
        Procesar múltiples documentos de una persona y consolidar

        Args:
            files: Lista de archivos PDF
            person_id: ID de la persona
            empresa: Nombre de la empresa
            documento: Documento del empleado

        Returns:
            JSON consolidado

        Raises:
            ValueError: Si la consolidación falla
        """
        logger.info(f"Procesando {len(files)} archivos para consolidación")

        # Procesar cada documento individualmente
        individual_results = []
        failed_files = []

        for i, file in enumerate(files, 1):
            try:
                logger.info(f"Procesando archivo {i}/{len(files)}: {file.filename}")
                # No guardar archivos individuales (save=False), solo procesarlos para consolidar
                result = self.process_single_document(file, save=False)
                individual_results.append(result)
                logger.info(f"✓ Archivo {i} procesado exitosamente")
            except Exception as e:
                logger.error(f"✗ Error procesando archivo {file.filename}: {str(e)}")
                failed_files.append((file.filename, str(e)))
                # Continuar con los demás archivos

        if not individual_results:
            error_msg = "No se pudo procesar ningún archivo. Errores: " + "; ".join(
                [f"{fname}: {err}" for fname, err in failed_files]
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        if failed_files:
            logger.warning(f"Se procesaron {len(individual_results)}/{len(files)} archivos. "
                          f"Fallaron: {[fname for fname, _ in failed_files]}")

        # Consolidar resultados
        try:
            logger.info(f"Iniciando consolidación de {len(individual_results)} historias")
            consolidated = self._consolidate_historias(individual_results, person_id)
            logger.info("✓ Consolidación completada exitosamente")
        except Exception as e:
            logger.error(f"✗ Error en consolidación: {str(e)}", exc_info=True)
            # Guardar archivo marcado como fallido
            failed_id = str(uuid.uuid4())
            failed_path = self.processed_folder / f"{failed_id}_FAILED.json"
            with open(failed_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'error': str(e),
                    'archivos_intentados': [h.get('archivo_origen') for h in individual_results],
                    'fecha_error': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            raise ValueError(f"Error consolidando historias: {str(e)}")

        # Guardar consolidado
        file_id = str(uuid.uuid4())
        consolidated['id_procesamiento'] = file_id

        # Agregar metadata de empresa y documento en datos_empleado
        if 'datos_empleado' not in consolidated:
            consolidated['datos_empleado'] = {}

        if empresa:
            consolidated['datos_empleado']['empresa'] = empresa
        if documento:
            consolidated['datos_empleado']['documento'] = documento

        consolidated_filename = f"{file_id}.json"
        consolidated_path = self.processed_folder / consolidated_filename

        with open(consolidated_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Consolidado guardado: {consolidated_filename}")
        logger.info(f"  - Documentos consolidados: {consolidated.get('num_documentos_consolidados', 0)}")
        logger.info(f"  - Diagnósticos: {len(consolidated.get('diagnosticos', []))}")
        logger.info(f"  - Recomendaciones: {len(consolidated.get('recomendaciones', []))}")
        logger.info(f"  - Remisiones: {len(consolidated.get('remisiones', []))}")
        logger.info(f"  - Alertas: {len(consolidated.get('alertas_validacion', []))}")

        return consolidated

    # ==================== MÉTODOS DE MERGE (consolidate_person.py) ====================

    def _merge_diagnosticos(self, historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge inteligente de diagnósticos evitando duplicados.
        Consolida por código CIE-10. Si hay duplicados, mantiene el de mayor confianza.
        """
        diagnosticos_dict = {}

        for historia in historias:
            for diag in historia.get('diagnosticos', []):
                codigo = diag.get('codigo_cie10')
                if not codigo:
                    continue

                # Si no existe, agregar
                if codigo not in diagnosticos_dict:
                    diagnosticos_dict[codigo] = diag
                else:
                    # Si existe, mantener el de mayor confianza
                    confianza_actual = diagnosticos_dict[codigo].get('confianza', 0.0)
                    confianza_nueva = diag.get('confianza', 0.0)

                    if confianza_nueva > confianza_actual:
                        diagnosticos_dict[codigo] = diag

        return list(diagnosticos_dict.values())

    def _merge_antecedentes(self, historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge inteligente de antecedentes evitando duplicados.
        Consolida por tipo + descripción (normalizada).
        """
        antecedentes_dict = {}

        for historia in historias:
            for ant in historia.get('antecedentes', []):
                tipo = ant.get('tipo', '')
                descripcion = ant.get('descripcion', '').strip().lower()

                if not descripcion:
                    continue

                # Clave única: tipo + descripción normalizada
                key = f"{tipo}:{descripcion}"

                # Si no existe, agregar
                if key not in antecedentes_dict:
                    antecedentes_dict[key] = ant
                else:
                    # Si existe, actualizar fecha si es más reciente
                    fecha_actual = antecedentes_dict[key].get('fecha_aproximada', '')
                    fecha_nueva = ant.get('fecha_aproximada', '')

                    if fecha_nueva and (not fecha_actual or fecha_nueva > fecha_actual):
                        antecedentes_dict[key] = ant

        return list(antecedentes_dict.values())

    def _es_examen_relevante(self, exam: Dict[str, Any]) -> bool:
        """
        Determina si un examen debe incluirse en el consolidado.

        INCLUIR si cumple al menos uno:
        - interpretacion ∈ {"alterado", "critico", "patologico"}
        - hallazgos_clave NO vacío
        - resultado NO vacío
        """
        interpretacion = (exam.get('interpretacion', '') or '').lower().strip()
        hallazgos = (exam.get('hallazgos_clave', '') or '').strip()
        resultado = (exam.get('resultado', '') or '').strip()

        # INCLUIR: interpretacion alterada/crítica/patológica
        if interpretacion in ['alterado', 'critico', 'patologico', 'anormal']:
            return True

        # INCLUIR: tiene hallazgos_clave no vacío
        if hallazgos and hallazgos.lower() not in ['normal', 'sin hallazgos', 'sin alteraciones']:
            return True

        # INCLUIR: tiene resultado no vacío
        if resultado and resultado.lower() not in ['normal', 'sin alteraciones']:
            return True

        # INCLUIR: no tiene interpretacion pero tiene texto no trivial
        if not interpretacion and (hallazgos or resultado):
            return True

        # EXCLUIR: solo si interpretacion=="normal" Y hallazgos/resultado vacíos o "normal"
        if interpretacion == 'normal':
            hallazgos_vacio_o_normal = (
                not hallazgos or
                hallazgos.lower() in ['normal', 'sin hallazgos', 'sin alteraciones', 'dentro de limites normales']
            )
            resultado_vacio_o_normal = (
                not resultado or
                resultado.lower() in ['normal', 'sin alteraciones', 'dentro de limites normales']
            )

            if hallazgos_vacio_o_normal and resultado_vacio_o_normal:
                return False  # Excluir

        # Default: incluir (conservador)
        return True

    def _merge_examenes(self, historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge inteligente de exámenes evitando duplicados.
        SOLO incluye exámenes con hallazgos anormales o clínicamente relevantes.
        """
        examenes_dict = {}

        for historia in historias:
            for exam in historia.get('examenes', []):
                tipo = exam.get('tipo', '')
                fecha = exam.get('fecha_realizacion', '')

                if not tipo:
                    continue

                # Filtrar: solo incluir exámenes relevantes
                if not self._es_examen_relevante(exam):
                    continue

                # Clave única: tipo + fecha
                key = f"{tipo}:{fecha}"

                # Agregar o sobrescribir (última versión gana)
                examenes_dict[key] = exam

        # Ordenar por fecha (más recientes primero)
        examenes_list = list(examenes_dict.values())
        examenes_list.sort(
            key=lambda x: x.get('fecha_realizacion', ''),
            reverse=True
        )

        return examenes_list

    def _merge_incapacidades(self, historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge de incapacidades sin duplicados.
        Consolida por fecha_inicio + tipo.
        """
        incapacidades_dict = {}

        for historia in historias:
            for incap in historia.get('incapacidades', []):
                fecha_inicio = incap.get('fecha_inicio', '')
                tipo = incap.get('tipo', '')

                if not fecha_inicio:
                    continue

                key = f"{fecha_inicio}:{tipo}"
                incapacidades_dict[key] = incap

        # Ordenar por fecha_inicio (más recientes primero)
        incapacidades_list = list(incapacidades_dict.values())
        incapacidades_list.sort(
            key=lambda x: x.get('fecha_inicio', ''),
            reverse=True
        )

        return incapacidades_list

    def _merge_recomendaciones(self, historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge inteligente de recomendaciones evitando duplicados.
        Consolida por tipo + descripción normalizada.
        """
        recomendaciones_dict = {}

        for historia in historias:
            for rec in historia.get('recomendaciones', []):
                tipo = rec.get('tipo', '')
                descripcion = rec.get('descripcion', '').strip().lower()

                if not descripcion:
                    continue

                key = f"{tipo}:{descripcion}"

                # Si no existe, agregar
                if key not in recomendaciones_dict:
                    recomendaciones_dict[key] = rec
                else:
                    # Si existe, mantener la de mayor prioridad
                    prioridades = {'alta': 3, 'media': 2, 'baja': 1}
                    prioridad_actual = prioridades.get(
                        recomendaciones_dict[key].get('prioridad', 'media'), 2
                    )
                    prioridad_nueva = prioridades.get(
                        rec.get('prioridad', 'media'), 2
                    )

                    if prioridad_nueva > prioridad_actual:
                        recomendaciones_dict[key] = rec

        return list(recomendaciones_dict.values())

    def _merge_remisiones(self, historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge de remisiones evitando duplicados.
        Consolida por especialidad + motivo.
        SANITIZADO: Maneja motivo=None sin explotar.
        """
        remisiones_dict = {}

        for historia in historias:
            for rem in historia.get('remisiones', []):
                # SANITIZACIÓN: Manejar None en especialidad y motivo
                especialidad = (rem.get('especialidad') or '').strip().lower()
                motivo = (rem.get('motivo') or '').strip().lower()

                if not especialidad:
                    continue

                key = f"{especialidad}:{motivo}"

                # Agregar o actualizar fecha si es más reciente
                if key not in remisiones_dict:
                    remisiones_dict[key] = rem
                else:
                    fecha_actual = remisiones_dict[key].get('fecha_planeada', '')
                    fecha_nueva = rem.get('fecha_planeada', '')

                    if fecha_nueva and (not fecha_actual or fecha_nueva > fecha_actual):
                        remisiones_dict[key] = rem

        return list(remisiones_dict.values())

    def _consolidate_historias(
        self,
        historias: List[Dict[str, Any]],
        person_id: str
    ) -> Dict[str, Any]:
        """
        Consolida múltiples historias clínicas en una sola.

        Versión COMPLETA con:
        - Merge de recomendaciones/remisiones
        - Aptitud laboral priorizada
        - Programas SVE
        - Validaciones clínicas
        - Filtrado de alertas

        Args:
            historias: Lista de historias individuales
            person_id: ID de la persona

        Returns:
            Historia consolidada

        Raises:
            ValueError: Si la consolidación falla
        """
        if not historias:
            raise ValueError("No hay historias para consolidar")

        logger.info(f"Consolidando {len(historias)} historias")

        # Separar HC completas/CMO de exámenes específicos
        hcs_completas = [h for h in historias if h.get('tipo_documento_fuente') in ['hc_completa', 'cmo']]
        examenes_especificos = [h for h in historias if h.get('tipo_documento_fuente') == 'examen_especifico']

        logger.info(f"  - HC completas/CMO: {len(hcs_completas)}")
        logger.info(f"  - Exámenes específicos: {len(examenes_especificos)}")

        # Usar HC completa como base si existe, sino la primera
        if hcs_completas:
            consolidada = hcs_completas[0].copy()
        else:
            consolidada = historias[0].copy()

        # ===== Merge de datos del empleado - PRIORIZAR HC COMPLETA =====
        datos_empleado = {}

        # Primero tomar de exámenes específicos (datos básicos)
        for historia in examenes_especificos:
            empleado = historia.get('datos_empleado', {})
            for key, value in empleado.items():
                if value is not None and value != "" and value != "Empleado":
                    datos_empleado[key] = value

        # Luego sobrescribir con datos de HC completas (más confiables)
        for historia in hcs_completas:
            empleado = historia.get('datos_empleado', {})
            for key, value in empleado.items():
                if value is not None and value != "" and value != "Empleado":
                    # Priorizar cargo específico sobre "Empleado" genérico
                    if key == 'cargo':
                        if value and value.lower() not in ['empleado', 'trabajador', 'personal']:
                            datos_empleado[key] = value
                    else:
                        datos_empleado[key] = value

        consolidada['datos_empleado'] = datos_empleado

        # ===== Merge de signos vitales - PRIORIZAR HC COMPLETA =====
        signos_vitales = None
        for historia in reversed(hcs_completas):  # Más reciente primero
            sv = historia.get('signos_vitales')
            if sv:
                signos_vitales = sv
                break

        # Si no hay en HC, tomar de exámenes (poco probable pero posible)
        if not signos_vitales:
            for historia in reversed(examenes_especificos):
                sv = historia.get('signos_vitales')
                if sv:
                    signos_vitales = sv
                    break

        consolidada['signos_vitales'] = signos_vitales

        # ===== Tipo EMO y fecha - PRIORIZAR HC COMPLETA =====
        for historia in hcs_completas:
            if historia.get('tipo_emo'):
                consolidada['tipo_emo'] = historia['tipo_emo']
                break

        for historia in hcs_completas:
            if historia.get('fecha_emo'):
                consolidada['fecha_emo'] = historia['fecha_emo']
                break

        # ===== Merge inteligente de campos con lógica de deduplicación =====
        logger.info("Ejecutando merges...")
        consolidada['diagnosticos'] = self._merge_diagnosticos(historias)
        consolidada['antecedentes'] = self._merge_antecedentes(historias)
        consolidada['examenes'] = self._merge_examenes(historias)
        consolidada['incapacidades'] = self._merge_incapacidades(historias)
        consolidada['recomendaciones'] = self._merge_recomendaciones(historias)
        consolidada['remisiones'] = self._merge_remisiones(historias)

        # IMPORTANTE: NO heredar alertas de documentos individuales
        # Las alertas se generarán solo sobre el consolidado final
        consolidada['alertas_validacion'] = []

        # ===== Aptitud laboral - PRIORIZAR HC COMPLETA/CMO =====
        aptitud_encontrada = False
        for historia in reversed(hcs_completas):  # Más reciente primero
            if historia.get('aptitud_laboral'):
                consolidada['aptitud_laboral'] = historia['aptitud_laboral']
                consolidada['restricciones_especificas'] = historia.get('restricciones_especificas')
                consolidada['genera_reincorporacion'] = historia.get('genera_reincorporacion', False)
                consolidada['causa_reincorporacion'] = historia.get('causa_reincorporacion')
                aptitud_encontrada = True
                logger.info(f"  Aptitud laboral: {consolidada['aptitud_laboral']}")
                break

        # Si no hay aptitud en HC completas, tomar de cualquier fuente (fallback)
        if not aptitud_encontrada:
            for historia in reversed(historias):
                if historia.get('aptitud_laboral'):
                    consolidada['aptitud_laboral'] = historia['aptitud_laboral']
                    consolidada['restricciones_especificas'] = historia.get('restricciones_especificas')
                    consolidada['genera_reincorporacion'] = historia.get('genera_reincorporacion', False)
                    consolidada['causa_reincorporacion'] = historia.get('causa_reincorporacion')
                    logger.info(f"  Aptitud laboral (fallback): {consolidada['aptitud_laboral']}")
                    break

        # ===== Programas SVE: unión de todos =====
        sve_set = set()
        for historia in historias:
            sve_set.update(historia.get('programas_sve', []))
        consolidada['programas_sve'] = sorted(list(sve_set))
        logger.info(f"  Programas SVE: {consolidada['programas_sve']}")

        # ===== Metadata de consolidación =====
        consolidada['archivos_origen_consolidados'] = [
            h.get('archivo_origen', 'desconocido') for h in historias
        ]
        consolidada['fecha_consolidacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        consolidada['num_documentos_consolidados'] = len(historias)

        # Recalcular confianza promedio
        confianzas = []
        for diag in consolidada.get('diagnosticos', []):
            confianzas.append(diag.get('confianza', 0.0))

        if confianzas:
            consolidada['confianza_extraccion'] = sum(confianzas) / len(confianzas)

        # ===== VALIDACIONES DEL CONSOLIDADO FINAL =====
        logger.info("Ejecutando validaciones del consolidado...")
        try:
            # Setear tipo de documento como consolidado
            consolidada['tipo_documento_fuente'] = 'consolidado'

            # PRE-PROCESAMIENTO del consolidado
            # Limpiar y validar datos ANTES de Pydantic
            alertas_preprocesamiento = []

            # 1. Validar y limpiar signos vitales
            consolidada = validate_signos_vitales(consolidada, alertas_preprocesamiento)

            # 2. Normalizar aptitud_laboral
            consolidada = normalize_aptitud_laboral(consolidada, alertas_preprocesamiento)

            # Convertir a objeto Pydantic para validar
            historia_obj = HistoriaClinicaEstructurada.model_validate(consolidada)

            # VALIDACIONES CLÍNICAS (solo en consolidado)
            # 1. Validaciones de completitud
            alertas_validacion = validate_historia_completa(historia_obj)

            # 2. Validación cruzada diagnóstico↔examen
            alertas_cruzadas = validate_diagnosis_exam_consistency(historia_obj)
            alertas_validacion.extend(alertas_cruzadas)

            # 3. Validar que exámenes críticos/alterados tengan reflejo
            alertas_hallazgos = validate_examenes_criticos_sin_reflejo(historia_obj)
            alertas_validacion.extend(alertas_hallazgos)

            # 4. Agregar alertas de pre-procesamiento
            alertas_validacion.extend(alertas_preprocesamiento)

            # 5. Filtrar con lista blanca clínica
            alertas_filtradas = filter_alerts(alertas_validacion, historia_obj)

            # Actualizar alertas en el dict
            consolidada['alertas_validacion'] = [
                {
                    'tipo': alerta.tipo,
                    'severidad': alerta.severidad,
                    'campo_afectado': alerta.campo_afectado,
                    'descripcion': alerta.descripcion,
                    'accion_sugerida': alerta.accion_sugerida
                }
                for alerta in alertas_filtradas
            ]

            logger.info(f"  ✓ Validaciones completadas: {len(alertas_filtradas)} alertas clínicas")

        except Exception as e:
            logger.warning(f"  ⚠️ Error en validaciones: {e}")
            # Si falla validación, dejar alertas vacías (ya están en [])

        return consolidada

    # ==================== MÉTODOS ORIGINALES (sin cambios) ====================

    def get_all_results(self) -> List[Dict[str, Any]]:
        """
        Obtener todos los resultados procesados

        Returns:
            Lista de JSONs
        """
        results = []

        for json_file in self.processed_folder.glob('*.json'):
            # Saltar archivos FAILED
            if '_FAILED.json' in json_file.name:
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception:
                continue

        return results

    def get_result_by_id(self, result_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener un resultado por ID

        Args:
            result_id: ID del procesamiento

        Returns:
            JSON del resultado o None si no existe
        """
        # Log de la búsqueda
        logger.info(f"Buscando resultado con ID: {result_id}")
        logger.info(f"Directorio de búsqueda: {self.processed_folder.absolute()}")

        # Primero intentar buscar por nombre de archivo
        result_path = self.processed_folder / f"{result_id}.json"
        logger.info(f"Intentando ruta directa: {result_path.absolute()}")

        if result_path.exists():
            logger.info(f"✓ Archivo encontrado por nombre: {result_path.name}")
            with open(result_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Si no existe, buscar en todos los archivos JSON
        # (para archivos antiguos guardados con nombre diferente)
        logger.info(f"Archivo no encontrado por nombre. Buscando en todos los archivos...")

        all_files = list(self.processed_folder.glob('*.json'))
        logger.info(f"Total de archivos JSON en directorio: {len(all_files)}")

        for json_file in all_files:
            # Saltar archivos FAILED
            if '_FAILED.json' in json_file.name:
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_id = data.get('id_procesamiento')
                    if file_id == result_id:
                        logger.info(f"✓ Encontrado en archivo: {json_file.name} (id_procesamiento coincide)")
                        return data
            except Exception as e:
                logger.warning(f"Error leyendo {json_file.name}: {e}")
                continue

        logger.error(f"✗ No se encontró ningún archivo con id_procesamiento={result_id}")
        return None

    def export_to_excel(self, result_ids: List[str] = None) -> Path:
        """
        Exportar resultados a Excel

        Args:
            result_ids: IDs a exportar (si None, exporta todos)

        Returns:
            Path al archivo Excel generado
        """
        # Obtener resultados a exportar
        if result_ids:
            results = []
            not_found_ids = []
            for result_id in result_ids:
                result = self.get_result_by_id(result_id)
                if result:
                    results.append(result)
                else:
                    not_found_ids.append(result_id)

            if not_found_ids:
                logger.warning(f"No se encontraron los siguientes IDs: {not_found_ids}")

            if not results and result_ids:
                raise ValueError(f"No se encontraron resultados para los IDs proporcionados: {result_ids}")
        else:
            results = self.get_all_results()

        if not results:
            raise ValueError("No hay resultados para exportar")

        # Convertir a objetos HistoriaClinicaEstructurada
        historias = []
        failed_validations = []
        for result in results:
            try:
                historia = HistoriaClinicaEstructurada(**result)
                historias.append(historia)
            except Exception as e:
                # Si falla la validación, registrar el error
                result_id = result.get('id_procesamiento', 'unknown')
                logger.warning(f"No se pudo validar resultado {result_id}: {str(e)}")
                failed_validations.append(result_id)
                continue

        if failed_validations:
            logger.warning(f"Se omitieron {len(failed_validations)} resultados con errores de validación")

        if not historias:
            raise ValueError(
                f"No se pudieron convertir los resultados a formato válido. "
                f"Todos los {len(results)} resultados tienen errores de validación."
            )

        # Exportar usando ExcelExporter
        try:
            exporter = ExcelExporter(self.processed_folder)
            excel_filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            excel_path = exporter.export(historias, excel_filename)

            if not excel_path or not excel_path.exists():
                raise ValueError("El archivo Excel no se generó correctamente")

            logger.info(f"Excel generado exitosamente: {excel_path} ({len(historias)} registros)")
            return excel_path
        except Exception as e:
            logger.error(f"Error al generar archivo Excel: {str(e)}")
            raise ValueError(f"Error al generar archivo Excel: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del procesamiento

        Returns:
            Diccionario con estadísticas
        """
        results = self.get_all_results()

        total = len(results)
        if total == 0:
            return {
                'total_procesados': 0,
                'confianza_promedio': 0,
                'alertas': {'alta': 0, 'media': 0, 'baja': 0},
                'diagnosticos_frecuentes': [],
                'distribucion_emo': {}
            }

        avg_confidence = sum(r.get('confianza_extraccion', 0) for r in results) / total

        # Contar alertas por severidad
        alertas_alta = sum(
            len([a for a in r.get('alertas_validacion', []) if a.get('severidad') == 'alta'])
            for r in results
        )
        alertas_media = sum(
            len([a for a in r.get('alertas_validacion', []) if a.get('severidad') == 'media'])
            for r in results
        )
        alertas_baja = sum(
            len([a for a in r.get('alertas_validacion', []) if a.get('severidad') == 'baja'])
            for r in results
        )

        # Contar diagnósticos más frecuentes
        diagnosticos_counter = Counter()
        for r in results:
            for diag in r.get('diagnosticos', []):
                codigo = diag.get('codigo_cie10')
                descripcion = diag.get('descripcion', '')
                if codigo:
                    diagnosticos_counter[(codigo, descripcion)] += 1

        diagnosticos_frecuentes = [
            {
                'codigo': codigo,
                'descripcion': desc,
                'frecuencia': count
            }
            for (codigo, desc), count in diagnosticos_counter.most_common(10)
        ]

        # Distribución por tipo EMO
        emo_counter = Counter()
        for r in results:
            tipo_emo = r.get('tipo_emo', 'desconocido')
            emo_counter[tipo_emo] += 1

        distribucion_emo = dict(emo_counter)

        return {
            'total_procesados': total,
            'confianza_promedio': round(avg_confidence, 2),
            'alertas': {
                'alta': alertas_alta,
                'media': alertas_media,
                'baja': alertas_baja
            },
            'diagnosticos_frecuentes': diagnosticos_frecuentes,
            'distribucion_emo': distribucion_emo
        }
