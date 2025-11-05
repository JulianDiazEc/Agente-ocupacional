"""
Configuración global del sistema de procesamiento de historias clínicas.

Carga variables de entorno desde archivo .env usando pydantic-settings.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.

    Lee variables de entorno desde .env automáticamente.
    """

    # ===================================================================
    # AZURE DOCUMENT INTELLIGENCE
    # ===================================================================
    azure_doc_intelligence_endpoint: str = Field(
        ...,
        description="Endpoint de Azure Document Intelligence"
    )
    azure_doc_intelligence_key: str = Field(
        ...,
        description="API Key de Azure Document Intelligence"
    )

    # ===================================================================
    # ANTHROPIC CLAUDE API
    # ===================================================================
    anthropic_api_key: str = Field(
        ...,
        description="API Key de Anthropic Claude"
    )
    claude_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Modelo de Claude a utilizar"
    )
    claude_max_tokens: int = Field(
        default=8000,
        ge=1000,
        le=200000,
        description="Máximo de tokens a generar"
    )
    claude_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Temperatura para generación (0.0 = determinístico)"
    )
    enable_prompt_caching: bool = Field(
        default=True,
        description="Habilitar prompt caching de Anthropic (reduce costos 90%)"
    )

    # ===================================================================
    # PROCESAMIENTO
    # ===================================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Nivel de logging"
    )
    processing_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=1800,
        description="Timeout en segundos para procesamiento de cada HC"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Número máximo de reintentos en caso de error"
    )
    retry_delay_seconds: int = Field(
        default=2,
        ge=1,
        le=60,
        description="Segundos de espera entre reintentos"
    )

    # ===================================================================
    # DIRECTORIOS
    # ===================================================================
    data_dir: Path = Field(
        default=Path("./data"),
        description="Directorio raíz de datos"
    )
    raw_dir: Path = Field(
        default=Path("./data/raw"),
        description="Directorio de PDFs originales"
    )
    processed_dir: Path = Field(
        default=Path("./data/processed"),
        description="Directorio de JSONs procesados"
    )
    labeled_dir: Path = Field(
        default=Path("./data/labeled"),
        description="Directorio de ground truth para evaluación"
    )
    log_dir: Path = Field(
        default=Path("./logs"),
        description="Directorio de archivos de log"
    )

    # ===================================================================
    # CONFIGURACIÓN AVANZADA
    # ===================================================================
    default_workers: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Número de workers para procesamiento en batch"
    )
    batch_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Tamaño de batch para procesamiento paralelo"
    )
    debug_mode: bool = Field(
        default=False,
        description="Habilitar modo debug (más verbose)"
    )
    save_intermediate_extractions: bool = Field(
        default=True,
        description="Guardar texto extraído por Azure (útil para debugging)"
    )

    # ===================================================================
    # VALIDACIÓN Y CALIDAD
    # ===================================================================
    min_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de confianza para aceptar extracción"
    )
    strict_cie10_validation: bool = Field(
        default=True,
        description="Habilitar validación estricta de códigos CIE-10"
    )
    enable_console_alerts: bool = Field(
        default=True,
        description="Mostrar alertas en consola durante procesamiento"
    )

    # Configuración de Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignorar variables de entorno adicionales
    )

    def ensure_directories(self) -> None:
        """
        Crea los directorios necesarios si no existen.

        Se ejecuta automáticamente al inicializar Settings.
        """
        directories = [
            self.data_dir,
            self.raw_dir,
            self.processed_dir,
            self.labeled_dir,
            self.log_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_prompt_path(self) -> Path:
        """Retorna la ruta al archivo de prompt maestro."""
        return Path("config/prompts/extraction_prompt.txt")

    def get_schema_path(self) -> Path:
        """Retorna la ruta al JSON Schema de salida."""
        return Path("config/schemas/output_schema.json")

    def validate_api_keys(self) -> None:
        """
        Valida que las API keys tengan formato correcto.

        Raises:
            ValueError: Si alguna API key no tiene el formato esperado
        """
        # Validar Azure endpoint
        if not self.azure_doc_intelligence_endpoint.startswith("https://"):
            raise ValueError(
                f"Azure endpoint debe comenzar con https://: "
                f"{self.azure_doc_intelligence_endpoint}"
            )

        # Validar Azure key (debe tener al menos 32 caracteres)
        if len(self.azure_doc_intelligence_key) < 32:
            raise ValueError(
                "Azure Document Intelligence key parece inválida (muy corta)"
            )

        # Validar Anthropic key
        if not self.anthropic_api_key.startswith("sk-ant-"):
            raise ValueError(
                "Anthropic API key debe comenzar con 'sk-ant-': "
                f"{self.anthropic_api_key[:10]}..."
            )

    def __repr__(self) -> str:
        """Representación segura que oculta API keys."""
        return (
            f"Settings(\n"
            f"  azure_endpoint={self.azure_doc_intelligence_endpoint}\n"
            f"  azure_key=***HIDDEN***\n"
            f"  anthropic_key=***HIDDEN***\n"
            f"  claude_model={self.claude_model}\n"
            f"  log_level={self.log_level}\n"
            f"  data_dir={self.data_dir}\n"
            f")"
        )


# Singleton global de configuración
_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """
    Obtiene la instancia singleton de Settings.

    Carga las variables de entorno la primera vez que se llama,
    y retorna la misma instancia en llamadas subsecuentes.

    Returns:
        Settings: Instancia de configuración global

    Raises:
        ValueError: Si falta alguna variable de entorno requerida o
                   si las API keys no son válidas
    """
    global _settings_instance

    if _settings_instance is None:
        try:
            _settings_instance = Settings()
            _settings_instance.ensure_directories()
            _settings_instance.validate_api_keys()
        except Exception as e:
            raise ValueError(
                f"Error al cargar configuración. Verifique su archivo .env.\n"
                f"Error: {e}"
            ) from e

    return _settings_instance


def reload_settings() -> Settings:
    """
    Recarga la configuración desde el archivo .env.

    Útil para testing o para aplicar cambios sin reiniciar.

    Returns:
        Settings: Nueva instancia de configuración
    """
    global _settings_instance
    _settings_instance = None
    return get_settings()


# Exportar para importación conveniente
__all__ = ["Settings", "get_settings", "reload_settings"]
