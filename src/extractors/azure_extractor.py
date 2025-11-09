"""
Extractor de texto de PDFs usando Azure Document Intelligence (Form Recognizer).

Soporta PDFs nativos y escaneados con OCR de alta calidad.
"""

from pathlib import Path
from typing import Optional

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import get_settings
from src.extractors.base import ExtractionResult, PDFExtractor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AzureDocumentExtractor(PDFExtractor):
    """
    Extractor de PDFs usando Azure Document Intelligence.

    Utiliza el modelo "prebuilt-layout" para extracción de texto con OCR
    y detección de tablas estructuradas. Esto preserva la estructura
    de tablas que de otra forma se convertirían a texto lineal.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None,
        model_id: str = "prebuilt-layout"
    ):
        """
        Inicializa el cliente de Azure Document Intelligence.

        Args:
            endpoint: Endpoint de Azure (si None, usa el de settings)
            key: API Key de Azure (si None, usa el de settings)
            model_id: ID del modelo a usar (default: prebuilt-layout para tablas)
        """
        settings = get_settings()

        self.endpoint = endpoint or settings.azure_doc_intelligence_endpoint
        self.key = key or settings.azure_doc_intelligence_key
        self.model_id = model_id

        # Validar credenciales
        if not self.endpoint or not self.key:
            raise ValueError(
                "Azure Document Intelligence credentials no configuradas. "
                "Verifique AZURE_DOC_INTELLIGENCE_ENDPOINT y AZURE_DOC_INTELLIGENCE_KEY en .env"
            )

        # Crear cliente
        credential = AzureKeyCredential(self.key)
        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=credential
        )

        logger.info(
            f"AzureDocumentExtractor inicializado con endpoint: {self.endpoint}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrae texto de un PDF usando Azure Document Intelligence.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            ExtractionResult: Resultado de la extracción con texto y metadata

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo no es válido
            Exception: Si falla la llamada a Azure API
        """
        # Validar archivo
        self.validate_pdf(pdf_path)

        logger.info(f"Extrayendo texto de: {pdf_path.name}")

        try:
            # Leer archivo
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # Llamar a Azure API
            poller = self.client.begin_analyze_document(
                model_id=self.model_id,
                document=pdf_bytes
            )

            # Esperar resultado (puede tomar varios segundos)
            result = poller.result()

            # Extraer texto
            extracted_text = self._extract_text_from_result(result)

            # Formatear y agregar tablas estructuradas (si existen)
            tables_text = self._format_tables(result)
            if tables_text:
                # Agregar tablas al final del texto con separador claro
                extracted_text = f"{extracted_text}\n\n{'='*70}\nTABLAS ESTRUCTURADAS DETECTADAS:\n{tables_text}"

            # Calcular confianza promedio
            confidence = self._calculate_average_confidence(result)

            # Detectar si es documento escaneado
            is_scanned = self._is_scanned_document(result)

            # Metadata adicional
            table_count = len(result.tables) if hasattr(result, 'tables') and result.tables else 0
            metadata = {
                "page_count": len(result.pages),
                "model_id": self.model_id,
                "api_version": result.api_version if hasattr(result, 'api_version') else None,
                "table_count": table_count,
            }

            logger.info(
                f"Extracción exitosa: {len(extracted_text)} caracteres, "
                f"{len(result.pages)} páginas, {table_count} tabla(s), confianza: {confidence:.2f}"
            )

            return ExtractionResult(
                text=extracted_text,
                confidence=confidence,
                page_count=len(result.pages),
                is_scanned=is_scanned,
                metadata=metadata,
                error=None
            )

        except Exception as e:
            logger.error(f"Error en extracción de {pdf_path.name}: {e}")
            return ExtractionResult(
                text="",
                confidence=0.0,
                page_count=0,
                is_scanned=False,
                metadata=None,
                error=str(e)
            )

    def _extract_text_from_result(self, result) -> str:
        """
        Extrae todo el texto del resultado de Azure.

        Args:
            result: Resultado de begin_analyze_document()

        Returns:
            str: Texto completo extraído
        """
        if not result.content:
            # Fallback: extraer de páginas individuales
            pages_text = []
            for page in result.pages:
                page_text = []
                for line in page.lines:
                    page_text.append(line.content)
                pages_text.append("\n".join(page_text))
            return "\n\n".join(pages_text)

        return result.content

    def _format_tables(self, result) -> str:
        """
        Formatea tablas estructuradas para presentación legible.

        Extrae tablas detectadas por Azure y las formatea en texto estructurado
        que preserva filas y columnas, facilitando la interpretación correcta
        de checkboxes, opciones y valores tabulares.

        Args:
            result: Resultado de begin_analyze_document()

        Returns:
            str: Tablas formateadas como texto estructurado (vacío si no hay tablas)
        """
        if not hasattr(result, 'tables') or not result.tables:
            return ""

        formatted_tables = []

        for table_idx, table in enumerate(result.tables, 1):
            table_lines = [
                f"\n{'='*70}",
                f"[TABLA {table_idx}] - {table.row_count} filas x {table.column_count} columnas",
                f"{'='*70}"
            ]

            # Crear matriz de celdas
            cells_matrix = {}
            for cell in table.cells:
                row = cell.row_index
                col = cell.column_index
                content = cell.content.strip() if cell.content else ""
                cells_matrix[(row, col)] = content

            # Formatear como tabla legible
            for row in range(table.row_count):
                row_cells = []
                for col in range(table.column_count):
                    content = cells_matrix.get((row, col), "")
                    # Limitar ancho de celda para mejor visualización
                    content = content[:50] if len(content) > 50 else content
                    row_cells.append(content)

                # Formatear fila con separadores
                row_text = " | ".join(row_cells)
                table_lines.append(f"Fila {row + 1}: | {row_text} |")

            table_lines.append(f"{'='*70}\n")
            formatted_tables.append("\n".join(table_lines))

        tables_text = "\n".join(formatted_tables)

        if formatted_tables:
            logger.info(f"Formateadas {len(formatted_tables)} tabla(s) estructurada(s)")

        return tables_text

    def _calculate_average_confidence(self, result) -> float:
        """
        Calcula la confianza promedio del OCR.

        Args:
            result: Resultado de begin_analyze_document()

        Returns:
            float: Confianza promedio (0.0 - 1.0)
        """
        confidences = []

        for page in result.pages:
            for line in page.lines:
                if hasattr(line, 'confidence') and line.confidence is not None:
                    confidences.append(line.confidence)

        if not confidences:
            # Si no hay valores de confianza, asumir documento nativo (confianza alta)
            return 1.0

        return sum(confidences) / len(confidences)

    def _is_scanned_document(self, result) -> bool:
        """
        Detecta si el documento es escaneado o nativo.

        Los documentos escaneados tienen confianza OCR < 1.0.
        Los documentos nativos tienen confianza = 1.0 o None.

        Args:
            result: Resultado de begin_analyze_document()

        Returns:
            bool: True si es documento escaneado
        """
        for page in result.pages:
            for line in page.lines:
                if hasattr(line, 'confidence') and line.confidence is not None:
                    if line.confidence < 0.99:
                        return True
        return False

    def get_page_text(self, pdf_path: Path, page_number: int) -> str:
        """
        Extrae texto de una página específica.

        Args:
            pdf_path: Ruta al PDF
            page_number: Número de página (1-indexed)

        Returns:
            str: Texto de la página especificada
        """
        result = self.extract(pdf_path)

        if not result.success:
            raise ValueError(f"Error al extraer PDF: {result.error}")

        # Dividir por páginas (aproximado)
        pages = result.text.split("\n\n")

        if page_number < 1 or page_number > len(pages):
            raise ValueError(
                f"Número de página inválido: {page_number}. "
                f"El documento tiene {len(pages)} páginas."
            )

        return pages[page_number - 1]


__all__ = ["AzureDocumentExtractor"]
