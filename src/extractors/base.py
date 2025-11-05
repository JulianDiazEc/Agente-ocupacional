"""
Interface base para extractores de texto de PDFs.

Define el contrato que deben cumplir todos los extractors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ExtractionResult:
    """
    Resultado de la extracción de texto de un PDF.

    Attributes:
        text: Texto extraído del documento
        confidence: Confianza del OCR/extracción (0.0 - 1.0)
        page_count: Número de páginas procesadas
        is_scanned: Indica si el PDF es escaneado (requirió OCR)
        metadata: Metadata adicional del documento
        error: Mensaje de error si la extracción falló
    """
    text: str
    confidence: float = 1.0
    page_count: int = 0
    is_scanned: bool = False
    metadata: Optional[dict] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Indica si la extracción fue exitosa."""
        return self.error is None and len(self.text.strip()) > 0

    @property
    def word_count(self) -> int:
        """Cuenta de palabras en el texto extraído."""
        return len(self.text.split())


class PDFExtractor(ABC):
    """
    Clase abstracta base para extractores de PDFs.

    Cualquier implementación de extractor (Azure, Tesseract, etc.)
    debe heredar de esta clase e implementar extract().
    """

    @abstractmethod
    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extrae texto de un archivo PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            ExtractionResult: Resultado de la extracción

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo no es un PDF válido
        """
        pass

    def validate_pdf(self, pdf_path: Path) -> None:
        """
        Valida que el archivo existe y es un PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo no es un PDF
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")

        if not pdf_path.is_file():
            raise ValueError(f"La ruta no es un archivo: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"El archivo no es un PDF: {pdf_path}")


__all__ = ["PDFExtractor", "ExtractionResult"]
