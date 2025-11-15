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

# Importar módulos del CLI existente
from src.extractors.azure_extractor import AzureDocumentExtractor
from src.processors.claude_processor import ClaudeProcessor
from src.config.settings import settings


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
            extracted_text = self.extractor.extract(str(temp_path))

            # 2. Procesar con Claude
            processed_data = self.processor.process(extracted_text, filename)

            # 3. Guardar resultado
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

        # TODO: Implementar consolidación usando consolidate_person.py
        # Por ahora retornamos el primer resultado como placeholder

        consolidated = {
            'person_id': person_id,
            'num_documents_processed': len(files),
            'consolidated_data': individual_results[0] if individual_results else {},
            'individual_results': individual_results
        }

        # Guardar consolidado
        consolidated_filename = f"{person_id}_consolidated.json"
        consolidated_path = self.processed_folder / consolidated_filename

        with open(consolidated_path, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, ensure_ascii=False, indent=2)

        return consolidated

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
        # TODO: Implementar usando src/exporters/excel_exporter.py
        # Por ahora retornamos un placeholder

        excel_filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        excel_path = self.processed_folder / excel_filename

        # Placeholder: crear Excel vacío
        # En la implementación real, usar ExcelExporter del CLI

        return excel_path

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del procesamiento

        Returns:
            Diccionario con estadísticas
        """
        results = self.get_all_results()

        total = len(results)
        avg_confidence = sum(r.get('confianza_extraccion', 0) for r in results) / total if total > 0 else 0

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

        return {
            'total_procesados': total,
            'confianza_promedio': round(avg_confidence, 2),
            'alertas': {
                'alta': alertas_alta,
                'media': alertas_media,
                'baja': alertas_baja
            }
        }
