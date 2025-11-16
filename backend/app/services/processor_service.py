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

# Importar módulos del CLI existente
from src.extractors.azure_extractor import AzureDocumentExtractor
from src.processors.claude_processor import ClaudeProcessor
from src.exporters.excel_exporter import ExcelExporter
from src.config.schemas import HistoriaClinicaEstructurada


class ProcessorService:
    """Servicio de procesamiento de HCs"""

    def __init__(self):
        self.upload_folder = Path('backend/uploads')
        self.processed_folder = Path('backend/processed')

        # Asegurar que las carpetas existen
        self.upload_folder.mkdir(exist_ok=True, parents=True)
        self.processed_folder.mkdir(exist_ok=True, parents=True)

        # Inicializar procesadores (del CLI existente)
        self.extractor = AzureDocumentExtractor()
        self.processor = ClaudeProcessor()

    def process_single_document(self, file: FileStorage) -> Dict[str, Any]:
        """
        Procesar un solo documento PDF

        Args:
            file: Archivo PDF cargado

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

            # 4. Guardar resultado
            result_filename = f"{file_id}.json"
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
        person_id: str
    ) -> Dict[str, Any]:
        """
        Procesar múltiples documentos de una persona y consolidar

        Args:
            files: Lista de archivos PDF
            person_id: ID de la persona

        Returns:
            JSON consolidado
        """
        # Procesar cada documento individualmente
        individual_results = []

        for file in files:
            result = self.process_single_document(file)
            individual_results.append(result)

        # Consolidar resultados
        consolidated = self._consolidate_historias(individual_results, person_id)

        # Guardar consolidado
        file_id = str(uuid.uuid4())
        consolidated['id_procesamiento'] = file_id
        consolidated_filename = f"{file_id}.json"
        consolidated_path = self.processed_folder / consolidated_filename

        with open(consolidated_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, ensure_ascii=False, indent=2)

        return consolidated

    def _consolidate_historias(
        self,
        historias: List[Dict[str, Any]],
        person_id: str
    ) -> Dict[str, Any]:
        """
        Consolida múltiples historias de la misma persona

        Args:
            historias: Lista de historias individuales
            person_id: ID de la persona

        Returns:
            Historia consolidada
        """
        if not historias:
            raise ValueError("No hay historias para consolidar")

        # Usar la primera historia como base
        base = historias[0].copy()

        # Consolidar diagnósticos (evitar duplicados por código CIE-10)
        diagnosticos_dict = {}
        for historia in historias:
            for diag in historia.get('diagnosticos', []):
                codigo = diag.get('codigo_cie10')
                if not codigo:
                    continue

                # Si no existe o tiene mayor confianza, actualizar
                if codigo not in diagnosticos_dict:
                    diagnosticos_dict[codigo] = diag
                else:
                    if diag.get('confianza', 0) > diagnosticos_dict[codigo].get('confianza', 0):
                        diagnosticos_dict[codigo] = diag

        base['diagnosticos'] = list(diagnosticos_dict.values())

        # Consolidar exámenes (todos los exámenes relevantes)
        examenes = []
        for historia in historias:
            examenes.extend(historia.get('examenes', []))
        base['examenes'] = examenes

        # Consolidar antecedentes (evitar duplicados)
        antecedentes_set = set()
        antecedentes = []
        for historia in historias:
            for ant in historia.get('antecedentes', []):
                desc = ant.get('descripcion', '').strip().lower()
                tipo = ant.get('tipo', '')
                key = f"{tipo}:{desc}"
                if key not in antecedentes_set:
                    antecedentes_set.add(key)
                    antecedentes.append(ant)
        base['antecedentes'] = antecedentes

        # Consolidar alertas de validación
        alertas = []
        for historia in historias:
            alertas.extend(historia.get('alertas_validacion', []))
        base['alertas_validacion'] = alertas

        # Metadata de consolidación
        base['tipo_documento_fuente'] = 'consolidado'
        base['documentos_fuente'] = [h.get('archivo_origen', '') for h in historias]
        base['num_documentos_consolidados'] = len(historias)
        base['fecha_procesamiento'] = datetime.now().isoformat()

        return base

    def get_all_results(self) -> List[Dict[str, Any]]:
        """
        Obtener todos los resultados procesados

        Returns:
            Lista de JSONs
        """
        results = []

        for json_file in self.processed_folder.glob('*.json'):
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
        result_path = self.processed_folder / f"{result_id}.json"

        if not result_path.exists():
            return None

        with open(result_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def export_to_excel(self, result_ids: List[str] = None) -> Path:
        """
        Exportar resultados a Excel

        Args:
            result_ids: IDs a exportar (si None, exporta todos)

        Returns:
            Path al archivo Excel generado
        """
        from app import logger

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
