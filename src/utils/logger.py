"""
Sistema de logging centralizado con soporte para archivos y consola.

Usa Rich para output colorizado en consola y logging estándar para archivos.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_file_logging: bool = True,
) -> logging.Logger:
    """
    Configura un logger con handlers para consola (Rich) y archivo.

    Args:
        name: Nombre del logger (usualmente __name__)
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directorio donde guardar los logs (si None, usa ./logs)
        enable_file_logging: Si True, guarda logs en archivo además de consola

    Returns:
        logging.Logger: Logger configurado

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Sistema iniciado")
        >>> logger.warning("Advertencia detectada")
    """
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Evitar duplicar handlers si el logger ya fue configurado
    if logger.handlers:
        return logger

    # ==================================================================
    # HANDLER 1: Consola con Rich (colorizado)
    # ==================================================================
    console = Console(stderr=True)
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    rich_handler.setLevel(getattr(logging, log_level.upper()))

    # Formato para consola (Rich lo hace más bonito)
    rich_formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]"
    )
    rich_handler.setFormatter(rich_formatter)
    logger.addHandler(rich_handler)

    # ==================================================================
    # HANDLER 2: Archivo (opcional, para auditoría)
    # ==================================================================
    if enable_file_logging:
        if log_dir is None:
            log_dir = Path("./logs")

        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name.replace('.', '_')}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Siempre DEBUG en archivo

        # Formato detallado para archivo
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger ya configurado o crea uno nuevo.

    Wrapper conveniente para setup_logger con configuración por defecto.

    Args:
        name: Nombre del logger

    Returns:
        logging.Logger: Logger configurado
    """
    # Intenta obtener configuración global
    try:
        from src.config.settings import get_settings
        settings = get_settings()
        log_level = settings.log_level
        log_dir = settings.log_dir
    except Exception:
        # Fallback si no hay configuración disponible
        log_level = "INFO"
        log_dir = Path("./logs")

    return setup_logger(
        name=name,
        log_level=log_level,
        log_dir=log_dir,
        enable_file_logging=True
    )


# Logger por defecto para el módulo
logger = get_logger(__name__)


__all__ = ["setup_logger", "get_logger", "logger"]
