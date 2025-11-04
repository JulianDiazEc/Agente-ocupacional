"""
Procesador de historias clínicas usando Claude API (Anthropic).

Convierte texto extraído en estructuras validadas usando LLM.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from anthropic import Anthropic
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.schemas import HistoriaClinicaEstructurada
from src.config.settings import get_settings
from src.processors.prompts import get_extraction_prompt
from src.processors.validators import validate_historia_completa
from src.utils.helpers import safe_json_loads
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeProcessor:
    """
    Procesador de historias clínicas usando Claude API.

    Toma texto extraído por Azure y retorna HistoriaClinicaEstructurada.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        """
        Inicializa el procesador de Claude.

        Args:
            api_key: API key de Anthropic (si None, usa settings)
            model: Modelo a usar (si None, usa settings)
            max_tokens: Máximo de tokens (si None, usa settings)
            temperature: Temperatura (si None, usa settings)
        """
        settings = get_settings()

        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model
        self.max_tokens = max_tokens or settings.claude_max_tokens
        self.temperature = temperature or settings.claude_temperature

        # Validar API key
        if not self.api_key or not self.api_key.startswith("sk-ant-"):
            raise ValueError(
                "Anthropic API key inválida. "
                "Verifique ANTHROPIC_API_KEY en .env"
            )

        # Crear cliente
        self.client = Anthropic(api_key=self.api_key)

        logger.info(
            f"ClaudeProcessor inicializado con modelo: {self.model}, "
            f"max_tokens: {self.max_tokens}, temperature: {self.temperature}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def process(
        self,
        texto_extraido: str,
        archivo_origen: str,
        context: Optional[Dict[str, str]] = None
    ) -> HistoriaClinicaEstructurada:
        """
        Procesa texto extraído y retorna historia clínica estructurada.

        Args:
            texto_extraido: Texto extraído por Azure Document Intelligence
            archivo_origen: Nombre del archivo PDF original
            context: Contexto adicional (empresa, fecha, etc.)

        Returns:
            HistoriaClinicaEstructurada: Historia clínica validada

        Raises:
            ValueError: Si la respuesta de Claude no es válida
            ValidationError: Si el JSON no cumple el schema Pydantic
        """
        logger.info(f"Procesando historia clínica: {archivo_origen}")

        # Preparar context
        if context is None:
            context = {}
        context["archivo_origen"] = archivo_origen

        # Generar prompt
        prompt = get_extraction_prompt(
            texto_extraido=texto_extraido,
            context=context
        )

        logger.debug(f"Prompt generado: {len(prompt)} caracteres")

        try:
            # Llamar a Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extraer texto de la respuesta
            response_text = response.content[0].text

            logger.debug(f"Respuesta de Claude: {len(response_text)} caracteres")

            # Parsear JSON
            historia_dict = self._parse_claude_response(response_text)

            # Agregar metadata
            historia_dict["archivo_origen"] = archivo_origen

            # Validar contra schema Pydantic
            historia = HistoriaClinicaEstructurada.model_validate(historia_dict)

            # Ejecutar validaciones adicionales
            alertas_adicionales = validate_historia_completa(historia)

            # Agregar alertas de validación
            historia.alertas_validacion.extend(alertas_adicionales)

            # Calcular confianza si no fue calculada
            if historia.confianza_extraccion == 0.0:
                historia.confianza_extraccion = self._calculate_confidence(historia)

            logger.info(
                f"Procesamiento exitoso: {len(historia.diagnosticos)} diagnósticos, "
                f"{len(historia.examenes)} exámenes, "
                f"confianza: {historia.confianza_extraccion:.2f}, "
                f"{len(historia.alertas_validacion)} alertas"
            )

            return historia

        except Exception as e:
            logger.error(f"Error procesando {archivo_origen}: {e}")
            raise

    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta de Claude y extrae el JSON.

        Args:
            response_text: Texto de respuesta de Claude

        Returns:
            dict: Diccionario con la historia clínica

        Raises:
            ValueError: Si no se puede parsear el JSON
        """
        # Intentar parseo directo
        historia_dict = safe_json_loads(response_text)

        if historia_dict is not None:
            return historia_dict

        # Intentar extraer JSON si está embebido en texto
        # Buscar entre { y }
        start = response_text.find('{')
        end = response_text.rfind('}')

        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end + 1]
            historia_dict = safe_json_loads(json_str)

            if historia_dict is not None:
                return historia_dict

        # Si todo falla, lanzar error
        logger.error(f"No se pudo parsear respuesta de Claude: {response_text[:500]}...")
        raise ValueError(
            "La respuesta de Claude no contiene JSON válido. "
            "Verifique los logs para más detalles."
        )

    def _calculate_confidence(self, historia: HistoriaClinicaEstructurada) -> float:
        """
        Calcula la confianza global de la extracción.

        Args:
            historia: Historia clínica procesada

        Returns:
            float: Confianza promedio (0.0 - 1.0)
        """
        confidences = []

        # Confianza de diagnósticos
        for diag in historia.diagnosticos:
            confidences.append(diag.confianza)

        # Si no hay valores, asumir confianza media
        if not confidences:
            return 0.5

        return sum(confidences) / len(confidences)

    def process_batch(
        self,
        textos: list[tuple[str, str]],
        show_progress: bool = True
    ) -> list[HistoriaClinicaEstructurada]:
        """
        Procesa múltiples historias clínicas en batch.

        Args:
            textos: Lista de tuplas (texto_extraido, archivo_origen)
            show_progress: Mostrar barra de progreso

        Returns:
            list[HistoriaClinicaEstructurada]: Historias procesadas
        """
        historias = []

        if show_progress:
            try:
                from rich.progress import Progress, SpinnerColumn, TextColumn
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                ) as progress:
                    task = progress.add_task(
                        f"Procesando {len(textos)} historias clínicas...",
                        total=len(textos)
                    )

                    for texto, archivo in textos:
                        try:
                            historia = self.process(texto, archivo)
                            historias.append(historia)
                        except Exception as e:
                            logger.error(f"Error procesando {archivo}: {e}")
                        finally:
                            progress.update(task, advance=1)
            except ImportError:
                # Fallback sin progress bar
                for texto, archivo in textos:
                    try:
                        historia = self.process(texto, archivo)
                        historias.append(historia)
                    except Exception as e:
                        logger.error(f"Error procesando {archivo}: {e}")
        else:
            for texto, archivo in textos:
                try:
                    historia = self.process(texto, archivo)
                    historias.append(historia)
                except Exception as e:
                    logger.error(f"Error procesando {archivo}: {e}")

        logger.info(
            f"Batch completado: {len(historias)}/{len(textos)} historias procesadas exitosamente"
        )

        return historias


__all__ = ["ClaudeProcessor"]
