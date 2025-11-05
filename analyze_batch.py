#!/usr/bin/env python3
"""
Script de análisis estadístico para historias clínicas procesadas.

Genera estadísticas de calidad, alertas, diagnósticos y más.

Uso:
    python analyze_batch.py
    python analyze_batch.py --export estadisticas.xlsx
    python analyze_batch.py --dir ./custom_dir --export report.xlsx
"""

import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import click
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Importar desde el proyecto
sys.path.insert(0, str(Path(__file__).parent))

from src.config.schemas import HistoriaClinicaEstructurada
from src.exporters.json_exporter import load_historia_from_json
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class BatchAnalyzer:
    """Analizador de estadísticas de batch de historias clínicas."""

    def __init__(self, json_dir: Path):
        """
        Inicializa el analizador.

        Args:
            json_dir: Directorio con archivos JSON procesados
        """
        self.json_dir = Path(json_dir)
        self.historias: List[HistoriaClinicaEstructurada] = []
        self.stats: Dict = {}

    def load_historias(self) -> int:
        """
        Carga todas las historias clínicas desde JSONs.

        Returns:
            int: Número de historias cargadas exitosamente
        """
        json_files = list(self.json_dir.glob("*.json"))

        if not json_files:
            console.print(
                f"[yellow]No se encontraron archivos JSON en {self.json_dir}[/yellow]"
            )
            return 0

        console.print(f"\n[cyan]Cargando {len(json_files)} historias clínicas...[/cyan]")

        loaded = 0
        errors = 0

        for json_path in json_files:
            try:
                historia = load_historia_from_json(json_path)
                self.historias.append(historia)
                loaded += 1
            except Exception as e:
                logger.error(f"Error cargando {json_path.name}: {e}")
                errors += 1

        console.print(f"[green]✓ Cargadas: {loaded}[/green]")
        if errors > 0:
            console.print(f"[red]✗ Errores: {errors}[/red]")

        return loaded

    def calculate_statistics(self) -> Dict:
        """
        Calcula todas las estadísticas del batch.

        Returns:
            Dict: Diccionario con estadísticas calculadas
        """
        if not self.historias:
            return {}

        stats = {
            "total_historias": len(self.historias),
            "confianza": self._calculate_confidence_stats(),
            "alertas": self._calculate_alert_stats(),
            "campos_baja_confianza": self._calculate_low_confidence_fields(),
            "tipos_emo": self._calculate_emo_types(),
            "diagnosticos": self._calculate_diagnosis_stats(),
            "aptitud_laboral": self._calculate_aptitude_stats(),
            "programas_sve": self._calculate_sve_programs(),
            "examenes": self._calculate_exam_stats(),
        }

        self.stats = stats
        return stats

    def _calculate_confidence_stats(self) -> Dict:
        """Calcula estadísticas de confianza."""
        confidencias = [h.confianza_extraccion for h in self.historias]

        return {
            "promedio": sum(confidencias) / len(confidencias),
            "minima": min(confidencias),
            "maxima": max(confidencias),
            "por_debajo_70": sum(1 for c in confidencias if c < 0.7),
            "por_debajo_50": sum(1 for c in confidencias if c < 0.5),
        }

    def _calculate_alert_stats(self) -> Dict:
        """Calcula estadísticas de alertas."""
        alertas_por_severidad = {"alta": 0, "media": 0, "baja": 0}
        alertas_por_tipo = Counter()
        descripciones_alertas = []

        for historia in self.historias:
            for alerta in historia.alertas_validacion:
                alertas_por_severidad[alerta.severidad] += 1
                alertas_por_tipo[alerta.tipo] += 1
                descripciones_alertas.append(alerta.descripcion)

        # Top 5 alertas más comunes
        top_alertas = alertas_por_tipo.most_common(5)

        return {
            "total": sum(alertas_por_severidad.values()),
            "por_severidad": alertas_por_severidad,
            "por_tipo": dict(alertas_por_tipo),
            "top_5": top_alertas,
            "historias_con_alertas": sum(
                1 for h in self.historias if len(h.alertas_validacion) > 0
            ),
            "historias_sin_alertas": sum(
                1 for h in self.historias if len(h.alertas_validacion) == 0
            ),
        }

    def _calculate_low_confidence_fields(self) -> Dict:
        """Calcula campos con baja confianza más frecuentes."""
        campos_counter = Counter()

        for historia in self.historias:
            for campo in historia.campos_con_baja_confianza:
                campos_counter[campo] += 1

        return {
            "total_campos": sum(campos_counter.values()),
            "campos_unicos": len(campos_counter),
            "top_10": campos_counter.most_common(10),
        }

    def _calculate_emo_types(self) -> Dict:
        """Calcula distribución de tipos de EMO."""
        tipos = Counter(h.tipo_emo for h in self.historias if h.tipo_emo)

        return {
            "distribucion": dict(tipos),
            "sin_tipo": sum(1 for h in self.historias if h.tipo_emo is None),
        }

    def _calculate_diagnosis_stats(self) -> Dict:
        """Calcula estadísticas de diagnósticos."""
        cie10_counter = Counter()
        diagnosticos_relacionados_trabajo = 0
        total_diagnosticos = 0

        for historia in self.historias:
            total_diagnosticos += len(historia.diagnosticos)
            for diag in historia.diagnosticos:
                cie10_counter[f"{diag.codigo_cie10} - {diag.descripcion}"] += 1
                if diag.relacionado_trabajo:
                    diagnosticos_relacionados_trabajo += 1

        return {
            "total": total_diagnosticos,
            "promedio_por_historia": (
                total_diagnosticos / len(self.historias) if self.historias else 0
            ),
            "relacionados_trabajo": diagnosticos_relacionados_trabajo,
            "top_10_cie10": cie10_counter.most_common(10),
            "historias_sin_diagnosticos": sum(
                1 for h in self.historias if len(h.diagnosticos) == 0
            ),
        }

    def _calculate_aptitude_stats(self) -> Dict:
        """Calcula estadísticas de aptitud laboral."""
        aptitudes = Counter(h.aptitud_laboral for h in self.historias if h.aptitud_laboral)

        return {
            "distribucion": dict(aptitudes),
            "sin_aptitud": sum(1 for h in self.historias if h.aptitud_laboral is None),
            "con_restricciones": sum(
                1
                for h in self.historias
                if h.restricciones_especificas is not None
            ),
        }

    def _calculate_sve_programs(self) -> Dict:
        """Calcula estadísticas de programas SVE."""
        sve_counter = Counter()

        for historia in self.historias:
            for programa in historia.programas_sve:
                sve_counter[programa] += 1

        return {
            "total_asignaciones": sum(sve_counter.values()),
            "distribucion": dict(sve_counter),
            "top_5": sve_counter.most_common(5),
            "historias_sin_sve": sum(
                1 for h in self.historias if len(h.programas_sve) == 0
            ),
        }

    def _calculate_exam_stats(self) -> Dict:
        """Calcula estadísticas de exámenes."""
        tipos_examenes = Counter()
        total_examenes = 0

        for historia in self.historias:
            total_examenes += len(historia.examenes)
            for examen in historia.examenes:
                tipos_examenes[examen.tipo] += 1

        return {
            "total": total_examenes,
            "promedio_por_historia": (
                total_examenes / len(self.historias) if self.historias else 0
            ),
            "por_tipo": dict(tipos_examenes),
        }

    def display_results(self) -> None:
        """Muestra resultados en terminal con Rich."""
        if not self.stats:
            console.print("[yellow]No hay estadísticas para mostrar[/yellow]")
            return

        console.print("\n" + "=" * 80)
        console.print(
            Panel.fit(
                "[bold cyan]ANÁLISIS DE BATCH - HISTORIAS CLÍNICAS PROCESADAS[/bold cyan]",
                border_style="cyan",
            )
        )
        console.print("=" * 80 + "\n")

        # 1. Resumen General
        self._display_general_summary()

        # 2. Confianza de Extracción
        self._display_confidence_stats()

        # 3. Alertas de Validación
        self._display_alert_stats()

        # 4. Campos con Baja Confianza
        self._display_low_confidence_fields()

        # 5. Tipos de EMO
        self._display_emo_types()

        # 6. Diagnósticos CIE-10
        self._display_diagnosis_stats()

        # 7. Aptitud Laboral
        self._display_aptitude_stats()

        # 8. Programas SVE
        self._display_sve_programs()

        # 9. Exámenes
        self._display_exam_stats()

    def _display_general_summary(self) -> None:
        """Muestra resumen general."""
        console.print("[bold green]📊 RESUMEN GENERAL[/bold green]\n")

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="bold white")

        table.add_row("Total de HCs procesadas:", f"{self.stats['total_historias']}")
        table.add_row(
            "Confianza promedio:",
            f"{self.stats['confianza']['promedio']:.2%}",
        )
        table.add_row("Total de alertas:", f"{self.stats['alertas']['total']}")
        table.add_row(
            "Total de diagnósticos:", f"{self.stats['diagnosticos']['total']}"
        )

        console.print(table)
        console.print()

    def _display_confidence_stats(self) -> None:
        """Muestra estadísticas de confianza."""
        console.print("[bold yellow]🎯 CONFIANZA DE EXTRACCIÓN[/bold yellow]\n")

        conf = self.stats["confianza"]

        table = Table(show_header=True, box=None, padding=(0, 2))
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="bold")

        table.add_row("Promedio", f"{conf['promedio']:.2%}")
        table.add_row("Mínima", f"{conf['minima']:.2%}")
        table.add_row("Máxima", f"{conf['maxima']:.2%}")
        table.add_row("HCs con confianza < 70%", str(conf["por_debajo_70"]))
        table.add_row("HCs con confianza < 50%", str(conf["por_debajo_50"]))

        console.print(table)
        console.print()

    def _display_alert_stats(self) -> None:
        """Muestra estadísticas de alertas."""
        console.print("[bold red]⚠️  ALERTAS DE VALIDACIÓN[/bold red]\n")

        alerts = self.stats["alertas"]

        # Tabla de severidad
        table = Table(title="Alertas por Severidad", show_header=True)
        table.add_column("Severidad", style="bold")
        table.add_column("Cantidad", justify="right")
        table.add_column("% del Total", justify="right")

        total_alertas = alerts["total"]

        for severidad, cantidad in alerts["por_severidad"].items():
            porcentaje = (cantidad / total_alertas * 100) if total_alertas > 0 else 0

            # Color según severidad
            if severidad == "alta":
                severidad_str = f"[red]{severidad.upper()}[/red]"
            elif severidad == "media":
                severidad_str = f"[yellow]{severidad.upper()}[/yellow]"
            else:
                severidad_str = severidad

            table.add_row(severidad_str, str(cantidad), f"{porcentaje:.1f}%")

        console.print(table)

        # Top 5 alertas más comunes
        if alerts["top_5"]:
            console.print("\n[bold]Top 5 Tipos de Alertas:[/bold]\n")

            for i, (tipo, cantidad) in enumerate(alerts["top_5"], 1):
                console.print(f"  {i}. {tipo}: [bold]{cantidad}[/bold]")

        console.print(
            f"\n  • HCs con alertas: {alerts['historias_con_alertas']}"
        )
        console.print(
            f"  • HCs sin alertas: {alerts['historias_sin_alertas']}"
        )
        console.print()

    def _display_low_confidence_fields(self) -> None:
        """Muestra campos con baja confianza."""
        console.print("[bold magenta]📉 CAMPOS CON BAJA CONFIANZA[/bold magenta]\n")

        campos = self.stats["campos_baja_confianza"]

        console.print(f"Total de campos con baja confianza: {campos['total_campos']}")
        console.print(f"Campos únicos afectados: {campos['campos_unicos']}\n")

        if campos["top_10"]:
            table = Table(title="Top 10 Campos Más Afectados", show_header=True)
            table.add_column("#", style="dim", width=3)
            table.add_column("Campo", style="cyan")
            table.add_column("Frecuencia", justify="right", style="bold")

            for i, (campo, freq) in enumerate(campos["top_10"], 1):
                table.add_row(str(i), campo, str(freq))

            console.print(table)

        console.print()

    def _display_emo_types(self) -> None:
        """Muestra distribución de tipos de EMO."""
        console.print("[bold blue]📋 TIPOS DE EMO[/bold blue]\n")

        tipos = self.stats["tipos_emo"]

        if tipos["distribucion"]:
            table = Table(show_header=True)
            table.add_column("Tipo de EMO", style="cyan")
            table.add_column("Cantidad", justify="right", style="bold")
            table.add_column("% del Total", justify="right")

            total = sum(tipos["distribucion"].values())

            for tipo, cantidad in sorted(
                tipos["distribucion"].items(), key=lambda x: x[1], reverse=True
            ):
                porcentaje = (cantidad / total * 100) if total > 0 else 0
                table.add_row(tipo or "No especificado", str(cantidad), f"{porcentaje:.1f}%")

            console.print(table)

        if tipos["sin_tipo"] > 0:
            console.print(f"\n  • HCs sin tipo de EMO: {tipos['sin_tipo']}")

        console.print()

    def _display_diagnosis_stats(self) -> None:
        """Muestra estadísticas de diagnósticos."""
        console.print("[bold green]🏥 DIAGNÓSTICOS (CIE-10)[/bold green]\n")

        diags = self.stats["diagnosticos"]

        # Resumen
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="bold")

        table.add_row("Total de diagnósticos:", str(diags["total"]))
        table.add_row(
            "Promedio por HC:", f"{diags['promedio_por_historia']:.1f}"
        )
        table.add_row(
            "Relacionados con trabajo:", str(diags["relacionados_trabajo"])
        )
        table.add_row(
            "HCs sin diagnósticos:", str(diags["historias_sin_diagnosticos"])
        )

        console.print(table)

        # Top 10 diagnósticos
        if diags["top_10_cie10"]:
            console.print("\n[bold]Top 10 Diagnósticos Más Frecuentes:[/bold]\n")

            top_table = Table(show_header=True)
            top_table.add_column("#", style="dim", width=3)
            top_table.add_column("Código CIE-10 - Descripción", style="cyan")
            top_table.add_column("Frecuencia", justify="right", style="bold")

            for i, (diagnostico, freq) in enumerate(diags["top_10_cie10"], 1):
                top_table.add_row(str(i), diagnostico, str(freq))

            console.print(top_table)

        console.print()

    def _display_aptitude_stats(self) -> None:
        """Muestra estadísticas de aptitud laboral."""
        console.print("[bold cyan]💼 APTITUD LABORAL[/bold cyan]\n")

        apt = self.stats["aptitud_laboral"]

        if apt["distribucion"]:
            table = Table(show_header=True)
            table.add_column("Aptitud", style="cyan")
            table.add_column("Cantidad", justify="right", style="bold")
            table.add_column("% del Total", justify="right")

            total = sum(apt["distribucion"].values())

            for aptitud, cantidad in sorted(
                apt["distribucion"].items(), key=lambda x: x[1], reverse=True
            ):
                porcentaje = (cantidad / total * 100) if total > 0 else 0
                table.add_row(aptitud, str(cantidad), f"{porcentaje:.1f}%")

            console.print(table)

        console.print(f"\n  • HCs sin aptitud definida: {apt['sin_aptitud']}")
        console.print(f"  • HCs con restricciones: {apt['con_restricciones']}")
        console.print()

    def _display_sve_programs(self) -> None:
        """Muestra estadísticas de programas SVE."""
        console.print("[bold yellow]🔬 PROGRAMAS SVE[/bold yellow]\n")

        sve = self.stats["programas_sve"]

        console.print(f"Total de asignaciones a SVE: {sve['total_asignaciones']}")
        console.print(f"HCs sin programas SVE: {sve['historias_sin_sve']}\n")

        if sve["top_5"]:
            table = Table(title="Top 5 Programas SVE", show_header=True)
            table.add_column("#", style="dim", width=3)
            table.add_column("Programa", style="cyan")
            table.add_column("Asignaciones", justify="right", style="bold")

            for i, (programa, cantidad) in enumerate(sve["top_5"], 1):
                table.add_row(str(i), programa.upper(), str(cantidad))

            console.print(table)

        console.print()

    def _display_exam_stats(self) -> None:
        """Muestra estadísticas de exámenes."""
        console.print("[bold magenta]🔍 EXÁMENES PARACLÍNICOS[/bold magenta]\n")

        exams = self.stats["examenes"]

        console.print(f"Total de exámenes: {exams['total']}")
        console.print(f"Promedio por HC: {exams['promedio_por_historia']:.1f}\n")

        if exams["por_tipo"]:
            table = Table(title="Exámenes por Tipo", show_header=True)
            table.add_column("Tipo de Examen", style="cyan")
            table.add_column("Cantidad", justify="right", style="bold")

            for tipo, cantidad in sorted(
                exams["por_tipo"].items(), key=lambda x: x[1], reverse=True
            ):
                table.add_row(tipo, str(cantidad))

            console.print(table)

        console.print()

    def export_to_excel(self, output_path: Path) -> None:
        """
        Exporta estadísticas a Excel.

        Args:
            output_path: Ruta del archivo Excel de salida
        """
        if not self.stats:
            console.print("[yellow]No hay estadísticas para exportar[/yellow]")
            return

        console.print(f"\n[cyan]Exportando estadísticas a {output_path}...[/cyan]")

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Hoja 1: Resumen General
            self._export_general_summary(writer)

            # Hoja 2: Confianza
            self._export_confidence(writer)

            # Hoja 3: Alertas
            self._export_alerts(writer)

            # Hoja 4: Diagnósticos
            self._export_diagnosis(writer)

            # Hoja 5: Aptitud Laboral
            self._export_aptitude(writer)

            # Hoja 6: Programas SVE
            self._export_sve(writer)

            # Hoja 7: Exámenes
            self._export_exams(writer)

        console.print(f"[green]✓ Exportado exitosamente a {output_path}[/green]\n")

    def _export_general_summary(self, writer) -> None:
        """Exporta resumen general a Excel."""
        data = {
            "Métrica": [
                "Total HCs",
                "Confianza Promedio",
                "Confianza Mínima",
                "Confianza Máxima",
                "Total Alertas",
                "Total Diagnósticos",
                "Total Exámenes",
            ],
            "Valor": [
                self.stats["total_historias"],
                f"{self.stats['confianza']['promedio']:.2%}",
                f"{self.stats['confianza']['minima']:.2%}",
                f"{self.stats['confianza']['maxima']:.2%}",
                self.stats["alertas"]["total"],
                self.stats["diagnosticos"]["total"],
                self.stats["examenes"]["total"],
            ],
        }

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="Resumen", index=False)

    def _export_confidence(self, writer) -> None:
        """Exporta estadísticas de confianza."""
        conf = self.stats["confianza"]

        data = {
            "Métrica": [
                "Promedio",
                "Mínima",
                "Máxima",
                "HCs < 70%",
                "HCs < 50%",
            ],
            "Valor": [
                conf["promedio"],
                conf["minima"],
                conf["maxima"],
                conf["por_debajo_70"],
                conf["por_debajo_50"],
            ],
        }

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="Confianza", index=False)

    def _export_alerts(self, writer) -> None:
        """Exporta estadísticas de alertas."""
        alerts = self.stats["alertas"]

        # Alertas por severidad
        data_severidad = {
            "Severidad": list(alerts["por_severidad"].keys()),
            "Cantidad": list(alerts["por_severidad"].values()),
        }

        df = pd.DataFrame(data_severidad)
        df.to_excel(writer, sheet_name="Alertas", index=False)

    def _export_diagnosis(self, writer) -> None:
        """Exporta estadísticas de diagnósticos."""
        diags = self.stats["diagnosticos"]["top_10_cie10"]

        if diags:
            data = {
                "Diagnóstico": [d[0] for d in diags],
                "Frecuencia": [d[1] for d in diags],
            }

            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name="Diagnósticos", index=False)

    def _export_aptitude(self, writer) -> None:
        """Exporta estadísticas de aptitud."""
        apt = self.stats["aptitud_laboral"]["distribucion"]

        if apt:
            data = {"Aptitud": list(apt.keys()), "Cantidad": list(apt.values())}

            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name="Aptitud", index=False)

    def _export_sve(self, writer) -> None:
        """Exporta estadísticas de SVE."""
        sve = self.stats["programas_sve"]["distribucion"]

        if sve:
            data = {"Programa SVE": list(sve.keys()), "Cantidad": list(sve.values())}

            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name="Programas SVE", index=False)

    def _export_exams(self, writer) -> None:
        """Exporta estadísticas de exámenes."""
        exams = self.stats["examenes"]["por_tipo"]

        if exams:
            data = {
                "Tipo de Examen": list(exams.keys()),
                "Cantidad": list(exams.values()),
            }

            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name="Exámenes", index=False)


@click.command()
@click.option(
    "--dir",
    "-d",
    "json_dir",
    type=click.Path(exists=True),
    default="data/processed",
    help="Directorio con archivos JSON procesados (default: data/processed)",
)
@click.option(
    "--export",
    "-e",
    "export_path",
    type=click.Path(),
    help="Exportar estadísticas a Excel (ej: estadisticas.xlsx)",
)
def main(json_dir: str, export_path: Optional[str]) -> None:
    """
    Analiza historias clínicas procesadas y genera estadísticas.

    Ejemplos:

        python analyze_batch.py

        python analyze_batch.py --export estadisticas.xlsx

        python analyze_batch.py --dir ./custom_dir --export report.xlsx
    """
    try:
        # Crear analizador
        analyzer = BatchAnalyzer(Path(json_dir))

        # Cargar historias
        loaded = analyzer.load_historias()

        if loaded == 0:
            console.print("[red]No se pudieron cargar historias clínicas[/red]")
            return

        # Calcular estadísticas
        analyzer.calculate_statistics()

        # Mostrar resultados en terminal
        analyzer.display_results()

        # Exportar a Excel si se solicita
        if export_path:
            analyzer.export_to_excel(Path(export_path))

        console.print("[bold green]✓ Análisis completado exitosamente[/bold green]\n")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.exception("Error en análisis de batch")
        raise click.Abort()


if __name__ == "__main__":
    main()
