"""
Exportador de historias clínicas a formato JSON.

Guarda historias clínicas estructuradas en archivos JSON legibles.
"""

import json
from pathlib import Path
from typing import List

from src.config.schemas import HistoriaClinicaEstructurada
from src.utils.helpers import DateTimeEncoder
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JSONExporter:
    """
    Exportador de historias clínicas a JSON.

    Soporta export individual y en batch.
    """

    def __init__(self, output_dir: Path):
        """
        Inicializa el exportador.

        Args:
            output_dir: Directorio de salida para archivos JSON
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"JSONExporter inicializado con output_dir: {self.output_dir}")

    def export(
        self,
        historia: HistoriaClinicaEstructurada,
        filename: str | None = None,
        pretty: bool = True
    ) -> Path:
        """
        Exporta una historia clínica a JSON.

        Args:
            historia: Historia clínica a exportar
            filename: Nombre del archivo (si None, usa archivo_origen)
            pretty: Si True, formatea el JSON con indentación

        Returns:
            Path: Ruta al archivo JSON creado
        """
        # Determinar nombre de archivo
        if filename is None:
            # Extraer nombre base del archivo origen
            base_name = Path(historia.archivo_origen).stem
            filename = f"{base_name}.json"

        output_path = self.output_dir / filename

        # Convertir a diccionario
        historia_dict = historia.model_dump(mode='json')

        # Exportar
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(
                    historia_dict,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    cls=DateTimeEncoder
                )
            else:
                json.dump(
                    historia_dict,
                    f,
                    ensure_ascii=False,
                    cls=DateTimeEncoder
                )

        logger.info(f"Historia clínica exportada a: {output_path}")

        return output_path

    def export_batch(
        self,
        historias: List[HistoriaClinicaEstructurada],
        pretty: bool = True
    ) -> List[Path]:
        """
        Exporta múltiples historias clínicas.

        Args:
            historias: Lista de historias a exportar
            pretty: Si True, formatea el JSON con indentación

        Returns:
            List[Path]: Rutas a los archivos creados
        """
        output_paths = []

        for historia in historias:
            try:
                path = self.export(historia, pretty=pretty)
                output_paths.append(path)
            except Exception as e:
                logger.error(
                    f"Error exportando {historia.archivo_origen}: {e}"
                )

        logger.info(
            f"Batch export completado: {len(output_paths)}/{len(historias)} "
            f"historias exportadas"
        )

        return output_paths

    def export_consolidated(
        self,
        historias: List[HistoriaClinicaEstructurada],
        filename: str = "historias_consolidadas.json",
        pretty: bool = True
    ) -> Path:
        """
        Exporta múltiples historias en un solo archivo JSON.

        Args:
            historias: Lista de historias a exportar
            filename: Nombre del archivo consolidado
            pretty: Si True, formatea el JSON con indentación

        Returns:
            Path: Ruta al archivo JSON consolidado
        """
        output_path = self.output_dir / filename

        # Convertir todas las historias a diccionarios
        historias_dict = [h.model_dump(mode='json') for h in historias]

        # Exportar
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(
                    historias_dict,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    cls=DateTimeEncoder
                )
            else:
                json.dump(
                    historias_dict,
                    f,
                    ensure_ascii=False,
                    cls=DateTimeEncoder
                )

        logger.info(
            f"{len(historias)} historias exportadas a archivo consolidado: "
            f"{output_path}"
        )

        return output_path


def load_historia_from_json(json_path: Path) -> HistoriaClinicaEstructurada:
    """
    Carga una historia clínica desde un archivo JSON.

    Args:
        json_path: Ruta al archivo JSON

    Returns:
        HistoriaClinicaEstructurada: Historia clínica cargada

    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el JSON no es válido
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return HistoriaClinicaEstructurada.model_validate(data)


__all__ = ["JSONExporter", "load_historia_from_json"]
