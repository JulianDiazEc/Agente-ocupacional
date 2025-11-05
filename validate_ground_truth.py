#!/usr/bin/env python3
"""
Herramienta de validación y creación de ground truth para historias clínicas.

Permite revisar y corregir manualmente los JSONs procesados campo por campo,
generando ground truth validado para evaluación de calidad.

Uso:
    python validate_ground_truth.py data/raw/HC_001.pdf data/processed/HC_001.json
    python validate_ground_truth.py HC_001.pdf HC_001.json --output data/labeled/
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

# Importar desde el proyecto
sys.path.insert(0, str(Path(__file__).parent))

from src.config.schemas import HistoriaClinicaEstructurada
from src.exporters.json_exporter import load_historia_from_json
from src.extractors.azure_extractor import AzureDocumentExtractor
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class GroundTruthValidator:
    """
    Validador interactivo de historias clínicas para crear ground truth.
    """

    def __init__(
        self, pdf_path: Path, json_path: Path, output_dir: Path
    ):
        """
        Inicializa el validador.

        Args:
            pdf_path: Ruta al PDF original
            json_path: Ruta al JSON procesado
            output_dir: Directorio de salida para ground truth
        """
        self.pdf_path = Path(pdf_path)
        self.json_path = Path(json_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.texto_extraido: str = ""
        self.historia_original: HistoriaClinicaEstructurada = None
        self.historia_validada: Dict[str, Any] = {}

        # Estadísticas de validación
        self.stats = {
            "campos_validados": 0,
            "campos_editados": 0,
            "campos_saltados": 0,
            "total_campos": 0,
        }

        # Historial de correcciones
        self.correcciones: List[Dict] = []

    def load_data(self) -> bool:
        """
        Carga el PDF y el JSON procesado.

        Returns:
            bool: True si se cargó correctamente
        """
        try:
            # Cargar JSON procesado
            console.print(f"\n[cyan]Cargando JSON procesado: {self.json_path.name}[/cyan]")
            self.historia_original = load_historia_from_json(self.json_path)
            self.historia_validada = self.historia_original.model_dump(mode='json')

            # Extraer texto del PDF
            console.print(f"[cyan]Extrayendo texto del PDF: {self.pdf_path.name}[/cyan]")
            extractor = AzureDocumentExtractor()
            extraction_result = extractor.extract(self.pdf_path)

            if not extraction_result.success:
                console.print(f"[red]Error extrayendo PDF: {extraction_result.error}[/red]")
                return False

            self.texto_extraido = extraction_result.text

            console.print("[green]✓ Datos cargados exitosamente[/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]Error cargando datos: {e}[/red]")
            logger.exception("Error en load_data")
            return False

    def show_welcome(self) -> None:
        """Muestra pantalla de bienvenida."""
        console.clear()

        welcome = Panel.fit(
            "[bold cyan]VALIDADOR DE GROUND TRUTH[/bold cyan]\n\n"
            "Esta herramienta te permite validar manualmente campos extraídos\n"
            "de historias clínicas para crear ground truth de alta calidad.\n\n"
            "[bold]Opciones durante validación:[/bold]\n"
            "  [C]orrecto  - Marcar campo como válido\n"
            "  [E]ditar    - Corregir el valor del campo\n"
            "  [S]altar    - Revisar más tarde\n"
            "  [Q]uit      - Guardar y salir\n\n"
            "[dim]Navega campo por campo validando la información extraída.[/dim]",
            border_style="cyan",
            title="🔍 Validación de Historia Clínica",
        )

        console.print(welcome)
        console.print()

        # Mostrar información del archivo
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("Label", style="cyan")
        info_table.add_column("Value", style="bold white")

        info_table.add_row("PDF Original:", self.pdf_path.name)
        info_table.add_row("JSON Procesado:", self.json_path.name)
        info_table.add_row(
            "Archivo Origen:",
            self.historia_original.archivo_origen
        )
        info_table.add_row(
            "Confianza Global:",
            f"{self.historia_original.confianza_extraccion:.1%}"
        )

        console.print(info_table)
        console.print()

        if not Confirm.ask("[bold]¿Comenzar validación?[/bold]", default=True):
            raise KeyboardInterrupt("Validación cancelada por el usuario")

    def validate_field(
        self,
        field_name: str,
        field_value: Any,
        field_path: str,
        context: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> Tuple[str, Any]:
        """
        Valida un campo individual.

        Args:
            field_name: Nombre legible del campo
            field_value: Valor actual del campo
            field_path: Path en el JSON (ej: "datos_empleado.nombre_completo")
            context: Contexto del PDF relevante (opcional)
            confidence: Nivel de confianza (opcional)

        Returns:
            Tuple[str, Any]: ("correcto"|"editado"|"saltado", nuevo_valor)
        """
        console.clear()

        # Header
        self._show_progress()

        # Campo actual
        console.print(f"\n[bold cyan]CAMPO:[/bold cyan] {field_name}")
        console.print(f"[dim]Path: {field_path}[/dim]\n")

        # Mostrar contexto del PDF si está disponible
        if context:
            console.print(Panel(
                self._highlight_context(context, str(field_value)),
                title="📄 Texto del PDF (contexto)",
                border_style="blue",
                padding=(1, 2),
            ))
            console.print()

        # Valor extraído
        value_style = "bold white"
        if confidence and confidence < 0.7:
            value_style = "bold yellow"

        value_text = Text()
        value_text.append("Valor Extraído: ", style="cyan")
        value_text.append(str(field_value) if field_value else "[null]", style=value_style)

        if confidence:
            conf_style = "green" if confidence >= 0.9 else ("yellow" if confidence >= 0.7 else "red")
            value_text.append(f"  (confianza: {confidence:.1%})", style=conf_style)

        console.print(value_text)
        console.print()

        # Opciones
        console.print("[bold]Opciones:[/bold]")
        console.print("  [C] Correcto  [E] Editar  [S] Saltar  [Q] Guardar y salir")
        console.print()

        while True:
            choice = Prompt.ask(
                "Selecciona",
                choices=["c", "e", "s", "q"],
                default="c",
                show_choices=False,
            ).lower()

            if choice == "c":
                return "correcto", field_value

            elif choice == "e":
                new_value = self._edit_field(field_name, field_value, field_path)
                if new_value != field_value:
                    self.correcciones.append({
                        "campo": field_name,
                        "path": field_path,
                        "valor_original": field_value,
                        "valor_corregido": new_value,
                        "timestamp": datetime.now().isoformat(),
                    })
                    return "editado", new_value
                else:
                    return "correcto", field_value

            elif choice == "s":
                return "saltado", field_value

            elif choice == "q":
                if Confirm.ask("\n[yellow]¿Guardar progreso y salir?[/yellow]", default=True):
                    raise KeyboardInterrupt("Guardado por el usuario")
                continue

    def _edit_field(self, field_name: str, current_value: Any, field_path: str) -> Any:
        """
        Permite editar un campo.

        Args:
            field_name: Nombre del campo
            current_value: Valor actual
            field_path: Path en el JSON

        Returns:
            Any: Nuevo valor (o el mismo si se cancela)
        """
        console.print()
        console.print(f"[bold yellow]EDITANDO: {field_name}[/bold yellow]")
        console.print(f"Valor actual: {current_value}")
        console.print()

        # Determinar tipo de campo para validación
        new_value_str = Prompt.ask(
            "Nuevo valor (Enter para cancelar)",
            default=str(current_value) if current_value else "",
        )

        if not new_value_str or new_value_str == str(current_value):
            return current_value

        # Intentar convertir al tipo correcto
        try:
            if isinstance(current_value, bool):
                new_value = new_value_str.lower() in ("true", "yes", "si", "1", "verdadero")
            elif isinstance(current_value, int):
                new_value = int(new_value_str)
            elif isinstance(current_value, float):
                new_value = float(new_value_str)
            elif current_value is None:
                # Si era null, mantener como string
                new_value = new_value_str if new_value_str != "null" else None
            else:
                new_value = new_value_str

            return new_value

        except ValueError:
            console.print(f"[red]Error: Valor inválido. Manteniendo original.[/red]")
            return current_value

    def _highlight_context(self, text: str, search_term: str) -> str:
        """
        Resalta el término buscado en el contexto.

        Args:
            text: Texto completo
            search_term: Término a resaltar

        Returns:
            str: Texto con término resaltado
        """
        if not search_term or search_term == "None":
            return text

        # Buscar término (case insensitive)
        import re
        pattern = re.compile(re.escape(str(search_term)), re.IGNORECASE)
        highlighted = pattern.sub(f"[bold yellow]{search_term}[/bold yellow]", text)

        return highlighted

    def _show_progress(self) -> None:
        """Muestra progreso de la validación."""
        total = self.stats["total_campos"]
        validados = self.stats["campos_validados"]
        editados = self.stats["campos_editados"]
        saltados = self.stats["campos_saltados"]

        progress_text = Text()
        progress_text.append("Progreso: ", style="bold")
        progress_text.append(f"{validados}/{total} campos", style="cyan")

        if editados > 0:
            progress_text.append(f"  |  ", style="dim")
            progress_text.append(f"{editados} editados", style="yellow")

        if saltados > 0:
            progress_text.append(f"  |  ", style="dim")
            progress_text.append(f"{saltados} saltados", style="red")

        console.print(progress_text)

    def validate_all_fields(self) -> None:
        """Valida todos los campos importantes de la historia clínica."""
        console.clear()
        console.print("\n[bold cyan]Iniciando validación de campos...[/bold cyan]\n")

        # Definir campos a validar (orden de prioridad)
        validation_order = [
            # 1. Datos del empleado
            ("datos_empleado", "nombre_completo", "Nombre Completo"),
            ("datos_empleado", "documento", "Documento"),
            ("datos_empleado", "tipo_documento", "Tipo de Documento"),
            ("datos_empleado", "cargo", "Cargo"),
            ("datos_empleado", "empresa", "Empresa"),

            # 2. Tipo y fecha EMO
            ("root", "tipo_emo", "Tipo de EMO"),
            ("root", "fecha_emo", "Fecha del EMO"),

            # 3. Aptitud laboral
            ("root", "aptitud_laboral", "Aptitud Laboral"),
            ("root", "restricciones_especificas", "Restricciones Específicas"),
        ]

        # Contar total de campos (incluyendo arrays)
        self.stats["total_campos"] = len(validation_order)
        self.stats["total_campos"] += len(self.historia_original.diagnosticos)
        self.stats["total_campos"] += min(3, len(self.historia_original.examenes))
        self.stats["total_campos"] += min(2, len(self.historia_original.recomendaciones))

        # Validar campos simples
        for section, field_name, display_name in validation_order:
            try:
                if section == "root":
                    field_value = getattr(self.historia_original, field_name)
                    field_path = field_name
                else:
                    section_obj = getattr(self.historia_original, section)
                    field_value = getattr(section_obj, field_name)
                    field_path = f"{section}.{field_name}"

                # Obtener contexto del PDF
                context = self._get_field_context(field_name, field_value)

                # Validar
                status, new_value = self.validate_field(
                    display_name,
                    field_value,
                    field_path,
                    context=context,
                )

                # Actualizar stats
                if status == "correcto":
                    self.stats["campos_validados"] += 1
                elif status == "editado":
                    self.stats["campos_validados"] += 1
                    self.stats["campos_editados"] += 1

                    # Actualizar en historia validada
                    if section == "root":
                        self.historia_validada[field_name] = new_value
                    else:
                        self.historia_validada[section][field_name] = new_value

                elif status == "saltado":
                    self.stats["campos_saltados"] += 1

            except KeyboardInterrupt:
                # Usuario quiere salir
                self._save_progress()
                raise

            except Exception as e:
                logger.error(f"Error validando {display_name}: {e}")
                continue

        # Validar diagnósticos (los 3 primeros)
        self._validate_diagnosticos()

        # Validar exámenes (los 3 primeros)
        self._validate_examenes()

        # Validar recomendaciones (las 2 primeras)
        self._validate_recomendaciones()

    def _validate_diagnosticos(self) -> None:
        """Valida los diagnósticos principales."""
        diagnosticos = self.historia_original.diagnosticos[:3]  # Top 3

        for i, diag in enumerate(diagnosticos):
            try:
                # Validar código CIE-10
                status_cie, new_cie = self.validate_field(
                    f"Diagnóstico {i+1} - Código CIE-10",
                    diag.codigo_cie10,
                    f"diagnosticos[{i}].codigo_cie10",
                    context=self._get_field_context("diagnostico", diag.codigo_cie10),
                    confidence=diag.confianza,
                )

                if status_cie == "editado":
                    self.historia_validada["diagnosticos"][i]["codigo_cie10"] = new_cie
                    self.stats["campos_editados"] += 1

                self.stats["campos_validados"] += 1

            except KeyboardInterrupt:
                self._save_progress()
                raise
            except Exception as e:
                logger.error(f"Error validando diagnóstico {i+1}: {e}")
                continue

    def _validate_examenes(self) -> None:
        """Valida los exámenes principales."""
        examenes = self.historia_original.examenes[:3]  # Top 3

        for i, exam in enumerate(examenes):
            try:
                status, new_result = self.validate_field(
                    f"Examen {i+1} - {exam.nombre}",
                    exam.resultado,
                    f"examenes[{i}].resultado",
                    context=self._get_field_context("examen", exam.nombre),
                )

                if status == "editado":
                    self.historia_validada["examenes"][i]["resultado"] = new_result
                    self.stats["campos_editados"] += 1

                self.stats["campos_validados"] += 1

            except KeyboardInterrupt:
                self._save_progress()
                raise
            except Exception as e:
                logger.error(f"Error validando examen {i+1}: {e}")
                continue

    def _validate_recomendaciones(self) -> None:
        """Valida las recomendaciones principales."""
        recomendaciones = self.historia_original.recomendaciones[:2]  # Top 2

        for i, rec in enumerate(recomendaciones):
            try:
                status, new_desc = self.validate_field(
                    f"Recomendación {i+1}",
                    rec.descripcion,
                    f"recomendaciones[{i}].descripcion",
                    context=None,
                )

                if status == "editado":
                    self.historia_validada["recomendaciones"][i]["descripcion"] = new_desc
                    self.stats["campos_editados"] += 1

                self.stats["campos_validados"] += 1

            except KeyboardInterrupt:
                self._save_progress()
                raise
            except Exception as e:
                logger.error(f"Error validando recomendación {i+1}: {e}")
                continue

    def _get_field_context(self, field_name: str, field_value: Any) -> str:
        """
        Obtiene contexto relevante del PDF para un campo.

        Args:
            field_name: Nombre del campo
            field_value: Valor del campo

        Returns:
            str: Contexto relevante del PDF (máximo 500 caracteres)
        """
        if not field_value or not self.texto_extraido:
            return ""

        search_term = str(field_value)

        # Buscar término en el texto
        import re
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        match = pattern.search(self.texto_extraido)

        if match:
            start = max(0, match.start() - 200)
            end = min(len(self.texto_extraido), match.end() + 200)
            context = self.texto_extraido[start:end]

            # Limpiar
            context = context.replace("\n", " ").strip()

            # Agregar elipsis si es necesario
            if start > 0:
                context = "..." + context
            if end < len(self.texto_extraido):
                context = context + "..."

            return context

        return ""

    def _save_progress(self) -> None:
        """Guarda progreso actual."""
        console.print("\n[yellow]Guardando progreso...[/yellow]")
        self.save_ground_truth()

    def save_ground_truth(self) -> Path:
        """
        Guarda el ground truth validado.

        Returns:
            Path: Ruta al archivo guardado
        """
        # Nombre del archivo
        base_name = self.json_path.stem
        output_path = self.output_dir / f"{base_name}.json"

        # Agregar metadata de validación
        self.historia_validada["_validation_metadata"] = {
            "validated_at": datetime.now().isoformat(),
            "validated_by": "manual_validation",
            "source_pdf": str(self.pdf_path),
            "source_json": str(self.json_path),
            "stats": self.stats,
        }

        # Guardar JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.historia_validada, f, ensure_ascii=False, indent=2)

        console.print(f"\n[green]✓ Ground truth guardado: {output_path}[/green]")

        return output_path

    def generate_validation_report(self) -> Path:
        """
        Genera reporte de validación.

        Returns:
            Path: Ruta al reporte generado
        """
        base_name = self.json_path.stem
        report_path = self.output_dir / f"{base_name}_validation_report.txt"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("REPORTE DE VALIDACIÓN DE GROUND TRUTH\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"PDF Original: {self.pdf_path.name}\n")
            f.write(f"JSON Procesado: {self.json_path.name}\n")
            f.write(f"Fecha de Validación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")

            # Estadísticas
            f.write("-" * 80 + "\n")
            f.write("ESTADÍSTICAS DE VALIDACIÓN\n")
            f.write("-" * 80 + "\n\n")

            total = self.stats["total_campos"]
            validados = self.stats["campos_validados"]
            editados = self.stats["campos_editados"]
            saltados = self.stats["campos_saltados"]

            f.write(f"Total de campos revisados:  {total}\n")
            f.write(f"Campos validados:           {validados} ({validados/total*100:.1f}%)\n")
            f.write(f"Campos editados:            {editados} ({editados/total*100:.1f}%)\n")
            f.write(f"Campos saltados:            {saltados} ({saltados/total*100:.1f}%)\n")
            f.write("\n")

            # Precisión
            if validados > 0:
                precision = ((validados - editados) / validados) * 100
                f.write(f"Precisión del sistema:      {precision:.1f}%\n")
                f.write(f"  (Campos correctos sin editar / Total validados)\n")
                f.write("\n")

            # Correcciones realizadas
            if self.correcciones:
                f.write("-" * 80 + "\n")
                f.write("CORRECCIONES REALIZADAS\n")
                f.write("-" * 80 + "\n\n")

                for i, corr in enumerate(self.correcciones, 1):
                    f.write(f"{i}. {corr['campo']}\n")
                    f.write(f"   Path: {corr['path']}\n")
                    f.write(f"   Original: {corr['valor_original']}\n")
                    f.write(f"   Corregido: {corr['valor_corregido']}\n")
                    f.write(f"   Timestamp: {corr['timestamp']}\n")
                    f.write("\n")

            # Campos con baja confianza original
            campos_baja_confianza = self.historia_original.campos_con_baja_confianza
            if campos_baja_confianza:
                f.write("-" * 80 + "\n")
                f.write("CAMPOS CON BAJA CONFIANZA (ORIGINAL)\n")
                f.write("-" * 80 + "\n\n")

                for campo in campos_baja_confianza:
                    f.write(f"  - {campo}\n")

                f.write("\n")

            # Alertas originales
            if self.historia_original.alertas_validacion:
                f.write("-" * 80 + "\n")
                f.write("ALERTAS DE VALIDACIÓN (ORIGINAL)\n")
                f.write("-" * 80 + "\n\n")

                for alerta in self.historia_original.alertas_validacion:
                    f.write(f"[{alerta.severidad.upper()}] {alerta.tipo}\n")
                    f.write(f"  Campo: {alerta.campo_afectado}\n")
                    f.write(f"  Descripción: {alerta.descripcion}\n")
                    f.write(f"  Acción sugerida: {alerta.accion_sugerida}\n")
                    f.write("\n")

        console.print(f"[green]✓ Reporte generado: {report_path}[/green]")

        return report_path

    def show_summary(self) -> None:
        """Muestra resumen final de la validación."""
        console.clear()

        summary_panel = Panel.fit(
            "[bold green]VALIDACIÓN COMPLETADA[/bold green]\n\n"
            f"Total campos revisados:  {self.stats['total_campos']}\n"
            f"Campos validados:        {self.stats['campos_validados']}\n"
            f"Campos editados:         {self.stats['campos_editados']}\n"
            f"Campos saltados:         {self.stats['campos_saltados']}\n\n"
            f"[bold]Precisión del sistema:[/bold] "
            f"{((self.stats['campos_validados'] - self.stats['campos_editados']) / max(self.stats['campos_validados'], 1)) * 100:.1f}%",
            border_style="green",
            title="✓ Resumen de Validación",
        )

        console.print("\n")
        console.print(summary_panel)
        console.print("\n")


@click.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.argument("json_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    "output_dir",
    type=click.Path(),
    default="data/labeled",
    help="Directorio de salida para ground truth (default: data/labeled)",
)
def main(pdf_path: str, json_path: str, output_dir: str) -> None:
    """
    Valida y crea ground truth de historias clínicas.

    Muestra cada campo del JSON procesado junto con el contexto del PDF
    original, permitiendo validar o corregir manualmente.

    Ejemplos:

        python validate_ground_truth.py data/raw/HC_001.pdf data/processed/HC_001.json

        python validate_ground_truth.py HC_001.pdf HC_001.json --output data/labeled/
    """
    try:
        # Crear validador
        validator = GroundTruthValidator(
            Path(pdf_path),
            Path(json_path),
            Path(output_dir),
        )

        # Cargar datos
        if not validator.load_data():
            console.print("[red]No se pudieron cargar los datos[/red]")
            return

        # Mostrar bienvenida
        validator.show_welcome()

        # Validar todos los campos
        validator.validate_all_fields()

        # Guardar ground truth
        validator.save_ground_truth()

        # Generar reporte
        validator.generate_validation_report()

        # Mostrar resumen
        validator.show_summary()

        console.print("[bold green]✓ Validación completada exitosamente[/bold green]\n")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Validación interrumpida. Progreso guardado.[/yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}\n")
        logger.exception("Error en validación")
        raise click.Abort()


if __name__ == "__main__":
    main()
