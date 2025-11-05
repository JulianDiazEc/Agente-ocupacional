"""
Interfaz de línea de comandos (CLI) para procesamiento de historias clínicas.

Comandos disponibles:
- process: Procesar una HC individual
- batch: Procesar múltiples HCs en batch
- show: Ver resumen de HC procesada
- evaluate: Validar contra ground truth
- evaluate-batch: Evaluar batch completo
- export-narah: Exportar a formato Narah
"""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from src.config.settings import get_settings
from src.exporters.excel_exporter import ExcelExporter
from src.exporters.json_exporter import JSONExporter, load_historia_from_json
from src.extractors.azure_extractor import AzureDocumentExtractor
from src.processors.claude_processor import ClaudeProcessor
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Narah HC Processor - Sistema de procesamiento de historias clínicas ocupacionales.

    Procesa PDFs de historias clínicas usando Azure Document Intelligence y Claude API.
    """
    pass


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option(
    '--output',
    '-o',
    type=click.Path(),
    help='Directorio de salida (default: data/processed/)'
)
@click.option(
    '--show-result',
    '-s',
    is_flag=True,
    help='Mostrar resumen del resultado'
)
@click.option(
    '--save-extraction',
    is_flag=True,
    help='Guardar texto extraído por Azure'
)
def process(
    pdf_path: str,
    output: Optional[str],
    show_result: bool,
    save_extraction: bool
):
    """
    Procesa una historia clínica individual.

    Ejemplo:
        python -m src.cli process data/raw/HC_001.pdf
        python -m src.cli process HC_001.pdf --output ./output --show-result
    """
    settings = get_settings()

    pdf_path = Path(pdf_path)
    output_dir = Path(output) if output else settings.processed_dir

    console.print(f"\n[bold cyan]Procesando:[/bold cyan] {pdf_path.name}")

    try:
        # Paso 1: Extracción con Azure
        console.print("[yellow]1/3[/yellow] Extrayendo texto con Azure Document Intelligence...")

        extractor = AzureDocumentExtractor()
        extraction_result = extractor.extract(pdf_path)

        if not extraction_result.success:
            console.print(f"[bold red]Error:[/bold red] {extraction_result.error}")
            return

        console.print(
            f"  ✓ Extraídos {extraction_result.word_count} palabras "
            f"({extraction_result.page_count} páginas)"
        )

        # Guardar texto extraído si se solicita
        if save_extraction:
            extraction_path = output_dir / f"{pdf_path.stem}_extraction.txt"
            extraction_path.parent.mkdir(parents=True, exist_ok=True)
            with open(extraction_path, 'w', encoding='utf-8') as f:
                f.write(extraction_result.text)
            console.print(f"  ✓ Texto extraído guardado en: {extraction_path}")

        # Paso 2: Procesamiento con Claude
        console.print("[yellow]2/3[/yellow] Procesando con Claude API...")

        processor = ClaudeProcessor()
        historia = processor.process(
            texto_extraido=extraction_result.text,
            archivo_origen=pdf_path.name
        )

        console.print(
            f"  ✓ Procesamiento exitoso (confianza: {historia.confianza_extraccion:.2%})"
        )

        # Paso 3: Exportación
        console.print("[yellow]3/3[/yellow] Exportando resultados...")

        exporter = JSONExporter(output_dir)
        output_path = exporter.export(historia)

        console.print(f"  ✓ Guardado en: {output_path}")

        # Mostrar resumen si se solicita
        if show_result:
            _show_historia_summary(historia)

        # Mostrar alertas si hay
        if historia.alertas_validacion:
            console.print(f"\n[bold yellow]⚠ {len(historia.alertas_validacion)} alertas generadas[/bold yellow]")
            _show_alertas_table(historia.alertas_validacion[:5])

            if len(historia.alertas_validacion) > 5:
                console.print(f"  ... y {len(historia.alertas_validacion) - 5} más")

        console.print("\n[bold green]✓ Procesamiento completado exitosamente[/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.exception("Error procesando historia clínica")
        raise click.Abort()


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option(
    '--output',
    '-o',
    type=click.Path(),
    help='Directorio de salida (default: data/processed/)'
)
@click.option(
    '--workers',
    '-w',
    type=int,
    default=5,
    help='Número de workers para procesamiento paralelo'
)
@click.option(
    '--pattern',
    '-p',
    default='*.pdf',
    help='Patrón de archivos a procesar (default: *.pdf)'
)
def batch(input_dir: str, output: Optional[str], workers: int, pattern: str):
    """
    Procesa múltiples historias clínicas en batch.

    Ejemplo:
        python -m src.cli batch data/raw/
        python -m src.cli batch data/raw/ --output ./output --workers 10
    """
    settings = get_settings()

    input_dir = Path(input_dir)
    output_dir = Path(output) if output else settings.processed_dir

    # Buscar PDFs
    pdf_files = list(input_dir.glob(pattern))

    if not pdf_files:
        console.print(f"[yellow]No se encontraron archivos con patrón '{pattern}' en {input_dir}[/yellow]")
        return

    console.print(f"\n[bold cyan]Procesando {len(pdf_files)} archivos...[/bold cyan]")

    # Inicializar componentes
    extractor = AzureDocumentExtractor()
    processor = ClaudeProcessor()
    exporter = JSONExporter(output_dir)

    # Procesar cada archivo
    historias_procesadas = []
    errores = 0

    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("Procesando...", total=len(pdf_files))

        for pdf_path in pdf_files:
            try:
                # Extraer
                extraction_result = extractor.extract(pdf_path)

                if not extraction_result.success:
                    logger.error(f"Error extrayendo {pdf_path.name}: {extraction_result.error}")
                    errores += 1
                    progress.update(task, advance=1)
                    continue

                # Procesar
                historia = processor.process(
                    texto_extraido=extraction_result.text,
                    archivo_origen=pdf_path.name
                )

                # Exportar
                exporter.export(historia)

                historias_procesadas.append(historia)

            except Exception as e:
                logger.error(f"Error procesando {pdf_path.name}: {e}")
                errores += 1

            progress.update(task, advance=1)

    # Resumen
    console.print(f"\n[bold green]✓ Procesamiento batch completado[/bold green]")
    console.print(f"  Procesadas exitosamente: {len(historias_procesadas)}")
    console.print(f"  Errores: {errores}")

    # Estadísticas
    if historias_procesadas:
        confianza_promedio = sum(h.confianza_extraccion for h in historias_procesadas) / len(historias_procesadas)
        console.print(f"  Confianza promedio: {confianza_promedio:.2%}")


@cli.command()
@click.argument('json_path', type=click.Path(exists=True))
def show(json_path: str):
    """
    Muestra resumen de una historia clínica procesada.

    Ejemplo:
        python -m src.cli show data/processed/HC_001.json
    """
    json_path = Path(json_path)

    try:
        historia = load_historia_from_json(json_path)
        _show_historia_summary(historia)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option(
    '--output',
    '-o',
    type=click.Path(),
    default='narah_import.xlsx',
    help='Archivo de salida (default: narah_import.xlsx)'
)
def export_narah(input_dir: str, output: str):
    """
    Exporta historias procesadas a formato Narah Metrics.

    Ejemplo:
        python -m src.cli export-narah data/processed/ --output narah.xlsx
    """
    input_dir = Path(input_dir)
    output_path = Path(output)

    # Cargar todas las historias JSON
    json_files = list(input_dir.glob('*.json'))

    if not json_files:
        console.print(f"[yellow]No se encontraron archivos JSON en {input_dir}[/yellow]")
        return

    console.print(f"\n[cyan]Cargando {len(json_files)} historias...[/cyan]")

    historias = []
    for json_path in json_files:
        try:
            historia = load_historia_from_json(json_path)
            historias.append(historia)
        except Exception as e:
            logger.error(f"Error cargando {json_path.name}: {e}")

    if not historias:
        console.print("[yellow]No se pudieron cargar historias[/yellow]")
        return

    # Exportar
    console.print(f"[cyan]Exportando a formato Narah...[/cyan]")

    exporter = ExcelExporter(output_path.parent)
    export_path = exporter.export_narah_format(historias, filename=output_path.name)

    console.print(f"\n[bold green]✓ Exportado exitosamente a: {export_path}[/bold green]")
    console.print(f"  Total de registros: {len(historias)}")


def _show_historia_summary(historia):
    """Muestra un resumen formateado de la historia clínica."""
    console.print("\n" + "=" * 80)
    console.print(f"[bold]HISTORIA CLÍNICA: {historia.archivo_origen}[/bold]")
    console.print("=" * 80)

    # Datos del empleado
    console.print("\n[bold cyan]DATOS DEL EMPLEADO[/bold cyan]")
    if historia.datos_empleado.nombre_completo:
        console.print(f"  Nombre: {historia.datos_empleado.nombre_completo}")
    if historia.datos_empleado.documento:
        console.print(f"  Documento: {historia.datos_empleado.documento}")
    if historia.datos_empleado.cargo:
        console.print(f"  Cargo: {historia.datos_empleado.cargo}")
    if historia.datos_empleado.empresa:
        console.print(f"  Empresa: {historia.datos_empleado.empresa}")

    # EMO
    console.print("\n[bold cyan]EXAMEN MÉDICO OCUPACIONAL[/bold cyan]")
    console.print(f"  Tipo: {historia.tipo_emo or 'No especificado'}")
    console.print(f"  Fecha: {historia.fecha_emo or 'No especificada'}")
    console.print(f"  Aptitud: {historia.aptitud_laboral or 'No especificada'}")

    if historia.restricciones_especificas:
        console.print(f"  Restricciones: {historia.restricciones_especificas}")

    # Diagnósticos
    if historia.diagnosticos:
        console.print(f"\n[bold cyan]DIAGNÓSTICOS ({len(historia.diagnosticos)})[/bold cyan]")
        for diag in historia.diagnosticos[:5]:
            console.print(f"  • {diag.codigo_cie10} - {diag.descripcion} ({diag.tipo})")
        if len(historia.diagnosticos) > 5:
            console.print(f"  ... y {len(historia.diagnosticos) - 5} más")

    # Exámenes
    if historia.examenes:
        console.print(f"\n[bold cyan]EXÁMENES ({len(historia.examenes)})[/bold cyan]")
        for exam in historia.examenes[:5]:
            console.print(f"  • {exam.nombre} ({exam.tipo})")
        if len(historia.examenes) > 5:
            console.print(f"  ... y {len(historia.examenes) - 5} más")

    # Programas SVE
    if historia.programas_sve:
        console.print(f"\n[bold cyan]PROGRAMAS SVE[/bold cyan]")
        console.print(f"  {', '.join(historia.programas_sve)}")

    # Metadata
    console.print(f"\n[bold cyan]CALIDAD DE EXTRACCIÓN[/bold cyan]")
    console.print(f"  Confianza: {historia.confianza_extraccion:.2%}")
    console.print(f"  Alertas: {len(historia.alertas_validacion)}")


def _show_alertas_table(alertas):
    """Muestra tabla de alertas."""
    table = Table(title="Alertas de Validación", show_header=True)

    table.add_column("Severidad", style="bold")
    table.add_column("Tipo")
    table.add_column("Campo")
    table.add_column("Descripción", max_width=50)

    for alerta in alertas:
        # Color según severidad
        if alerta.severidad == "alta":
            severidad_str = f"[red]{alerta.severidad.upper()}[/red]"
        elif alerta.severidad == "media":
            severidad_str = f"[yellow]{alerta.severidad.upper()}[/yellow]"
        else:
            severidad_str = alerta.severidad

        table.add_row(
            severidad_str,
            alerta.tipo,
            alerta.campo_afectado,
            alerta.descripcion
        )

    console.print(table)


if __name__ == '__main__':
    cli()
