#!/usr/bin/env python3
"""
Herramienta de validación COMPLETA de ground truth v2.0

Valida TODO el JSON por secciones con navegación interactiva.
Captura razones de cada corrección para análisis posterior.

Uso:
    python validate_ground_truth_v2.py data/raw/HC_001.pdf data/processed/HC_001.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

sys.path.insert(0, str(Path(__file__).parent))

from src.config.schemas import HistoriaClinicaEstructurada
from src.exporters.json_exporter import load_historia_from_json
from src.extractors.azure_extractor import AzureDocumentExtractor

console = Console()

# Categorías de razones de corrección
RAZON_CATEGORIAS = {
    "1": ("valor_generico_a_especifico", "Valor genérico → específico encontrado en documento"),
    "2": ("error_extraccion", "Error de extracción (dato estaba claro en PDF)"),
    "3": ("dato_faltante", "Dato faltante completado manualmente"),
    "4": ("falso_positivo", "Falso positivo (extracción incorrecta)"),
    "5": ("formato_incorrecto", "Formato incorrecto"),
    "6": ("otro", "Otro (especificar)"),
}


class ValidationSession:
    """Sesión de validación de ground truth."""

    def __init__(self, json_path: Path, pdf_dir: Path, output_dir: Path):
        self.json_path = Path(json_path)
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.historia_dict: Dict[str, Any] = {}

        # Múltiples PDFs para consolidados
        self.pdfs_texto: Dict[str, str] = {}  # {nombre_archivo: texto}
        self.pdfs_paths: Dict[str, Path] = {}  # {nombre_archivo: path}

        # Tracking de cambios
        self.correcciones: List[Dict] = []
        self.campos_editados = 0
        self.campos_eliminados = 0
        self.campos_agregados = 0

    def load_data(self) -> bool:
        """Carga JSON y auto-detecta PDFs desde archivos_origen_consolidados."""
        try:
            # Cargar JSON
            console.print(f"\n[cyan]📂 Cargando: {self.json_path.name}[/cyan]")
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.historia_dict = json.load(f)

            # Detectar si es consolidado
            archivos_origen = self.historia_dict.get('archivos_origen_consolidados', [])

            if not archivos_origen:
                # JSON individual (no consolidado)
                archivo_simple = self.historia_dict.get('archivo_origen')
                if archivo_simple:
                    archivos_origen = [archivo_simple]

            if not archivos_origen:
                console.print("[red]❌ No se encontraron archivos de origen en el JSON[/red]")
                return False

            console.print(f"[cyan]📄 Archivos de origen detectados: {len(archivos_origen)}[/cyan]")

            # Extraer cada PDF
            extractor = AzureDocumentExtractor()

            for nombre_archivo in archivos_origen:
                # Buscar PDF en pdf_dir
                pdf_path = self.pdf_dir / nombre_archivo

                if not pdf_path.exists():
                    console.print(f"[yellow]⚠️  No encontrado: {nombre_archivo} (buscando en {self.pdf_dir})[/yellow]")
                    continue

                console.print(f"[cyan]   • Extrayendo: {nombre_archivo}[/cyan]")
                result = extractor.extract(pdf_path)

                if not result.success:
                    console.print(f"[yellow]⚠️  Error extrayendo {nombre_archivo}: {result.error}[/yellow]")
                    continue

                self.pdfs_texto[nombre_archivo] = result.text
                self.pdfs_paths[nombre_archivo] = pdf_path

            if not self.pdfs_texto:
                console.print("[red]❌ No se pudo extraer ningún PDF[/red]")
                return False

            console.print(f"[green]✅ {len(self.pdfs_texto)} PDF(s) extraídos\n[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error cargando datos: {e}[/red]")
            return False

    def get_pdf_for_field(self, campo: str) -> Optional[str]:
        """
        Retorna el nombre del PDF más relevante para este campo.

        Lógica:
        - Campos generales (empleado, signos, antecedentes) → HC/CMO
        - Exámenes específicos → PDF del examen si es individual
        - Default → primer PDF (generalmente HC)
        """
        # Si solo hay 1 PDF, retornar ese
        if len(self.pdfs_texto) == 1:
            return list(self.pdfs_texto.keys())[0]

        # Buscar HC o CMO para campos generales
        if any(keyword in campo.lower() for keyword in [
            'datos_empleado', 'signos_vitales', 'antecedentes',
            'tipo_emo', 'fecha_emo', 'aptitud', 'hallazgos'
        ]):
            for nombre in self.pdfs_texto.keys():
                if any(keyword in nombre.upper() for keyword in ['HC', 'CMO', 'HISTORIA', 'CERTIFICADO']):
                    return nombre

        # Para exámenes, intentar buscar PDF específico
        if 'examenes' in campo.lower():
            # Extraer tipo de examen del campo si es posible
            # Por ahora, buscar primero examen específico que no sea HC
            for nombre in self.pdfs_texto.keys():
                if not any(keyword in nombre.upper() for keyword in ['HC', 'CMO']):
                    # Probablemente un examen específico
                    return nombre

        # Default: primer PDF (generalmente HC)
        return list(self.pdfs_texto.keys())[0] if self.pdfs_texto else None

    def mostrar_contexto_pdf(self, search_term: str = None, campo: str = None):
        """Muestra fragmento relevante del PDF más apropiado."""

        # Determinar qué PDF usar
        pdf_nombre = self.get_pdf_for_field(campo) if campo else list(self.pdfs_texto.keys())[0]

        if not pdf_nombre:
            console.print("[yellow]No hay PDFs cargados[/yellow]")
            return

        texto_pdf = self.pdfs_texto[pdf_nombre]

        if not search_term:
            # Mostrar primeras líneas
            lines = texto_pdf.split('\n')[:20]
            texto = '\n'.join(lines)
        else:
            # Buscar término y mostrar contexto
            lines = texto_pdf.split('\n')
            matching_lines = []
            for i, line in enumerate(lines):
                if search_term.lower() in line.lower():
                    # Contexto: 2 líneas antes y después
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    matching_lines.extend(lines[start:end])
                    matching_lines.append("---")

            texto = '\n'.join(matching_lines[:100]) if matching_lines else "No encontrado"

        console.print(Panel(
            texto,
            title=f"📄 Contexto del PDF: {pdf_nombre}",
            border_style="cyan",
            expand=False
        ))

    def registrar_correccion(self, campo: str, valor_original: Any, valor_nuevo: Any):
        """Registra una corrección con su razón."""

        console.print("\n[yellow]📝 ¿Por qué se corrigió este campo?[/yellow]")
        console.print()

        for key, (cat_id, desc) in RAZON_CATEGORIAS.items():
            console.print(f"  [{key}] {desc}")

        console.print()
        categoria_num = Prompt.ask(
            "Selecciona categoría",
            choices=list(RAZON_CATEGORIAS.keys()),
            default="2"
        )

        categoria_id, categoria_desc = RAZON_CATEGORIAS[categoria_num]

        descripcion_adicional = ""
        if categoria_id == "otro":
            descripcion_adicional = Prompt.ask("Describe la razón")
        else:
            descripcion_adicional = Prompt.ask(
                "Descripción adicional (opcional, Enter para omitir)",
                default=""
            )

        self.correcciones.append({
            "campo": campo,
            "valor_original": valor_original,
            "valor_nuevo": valor_nuevo,
            "razon_categoria": categoria_id,
            "razon_descripcion": descripcion_adicional if descripcion_adicional else categoria_desc,
            "timestamp": datetime.now().isoformat()
        })

    def validar_campo_simple(self, campo_nombre: str, valor_actual: Any, path: str = "") -> Any:
        """Valida un campo simple (string, int, bool, etc.)."""

        full_path = f"{path}.{campo_nombre}" if path else campo_nombre

        # Determinar PDF fuente para este campo
        pdf_fuente = self.get_pdf_for_field(full_path)

        # Mostrar valor actual
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="cyan bold")
        table.add_column("Value")
        table.add_row("Campo:", full_path)
        table.add_row("Valor:", str(valor_actual) if valor_actual is not None else "[dim]null[/dim]")
        if pdf_fuente:
            table.add_row("📄 Fuente:", f"[dim]{pdf_fuente}[/dim]")
        console.print(table)

        # Opciones
        console.print("\n[C]orrecto  [E]ditar  [S]kip  [P]DF context  [Q]uit")
        opcion = Prompt.ask("Acción", choices=["c", "e", "s", "p", "q"], default="c").lower()

        if opcion == "q":
            return None  # Señal para quit
        elif opcion == "s":
            return valor_actual
        elif opcion == "p":
            # Mostrar contexto del PDF
            search_term = Prompt.ask("Término a buscar en PDF", default=campo_nombre)
            self.mostrar_contexto_pdf(search_term, campo=full_path)
            return self.validar_campo_simple(campo_nombre, valor_actual, path)
        elif opcion == "e":
            # Editar valor
            console.print(f"\n[yellow]Editando: {full_path}[/yellow]")
            console.print(f"Valor actual: {valor_actual}")

            # Determinar tipo
            if isinstance(valor_actual, bool):
                nuevo_valor = Confirm.ask("Nuevo valor")
            elif isinstance(valor_actual, int):
                nuevo_valor = IntPrompt.ask("Nuevo valor", default=valor_actual if valor_actual else 0)
            elif isinstance(valor_actual, float):
                nuevo_valor = float(Prompt.ask("Nuevo valor", default=str(valor_actual if valor_actual else 0.0)))
            else:
                nuevo_valor = Prompt.ask("Nuevo valor", default=str(valor_actual) if valor_actual else "")
                if nuevo_valor == "":
                    nuevo_valor = None

            # Registrar corrección
            if nuevo_valor != valor_actual:
                self.registrar_correccion(full_path, valor_actual, nuevo_valor)
                self.campos_editados += 1

            return nuevo_valor
        else:  # 'c'
            return valor_actual

    def validar_dict(self, dict_data: Dict, nombre_seccion: str, path: str = "") -> Optional[Dict]:
        """Valida un diccionario completo."""

        console.print(f"\n{'='*60}")
        console.print(f"  [bold cyan]VALIDANDO: {nombre_seccion}[/bold cyan]")
        console.print(f"{'='*60}\n")

        if not dict_data or len(dict_data) == 0:
            console.print("[dim]Sección vacía[/dim]")
            if Confirm.ask("¿Saltar esta sección?", default=True):
                return dict_data

        resultado = {}

        for key, value in dict_data.items():
            # Skip campos meta
            if key in ['id_procesamiento', 'fecha_procesamiento']:
                resultado[key] = value
                continue

            if value is None or (isinstance(value, str) and value == ""):
                # Campo vacío
                console.print(f"\n[dim]{key}: null/empty[/dim]")
                if Confirm.ask(f"¿Agregar valor para {key}?", default=False):
                    nuevo_valor = Prompt.ask(f"Valor para {key}")
                    resultado[key] = nuevo_valor if nuevo_valor else None
                    if nuevo_valor:
                        self.campos_agregados += 1
                else:
                    resultado[key] = value
            elif isinstance(value, dict):
                # Dict anidado
                resultado[key] = self.validar_dict(value, key, f"{path}.{key}" if path else key)
                if resultado[key] is None:
                    return None  # Quit signal
            elif isinstance(value, list):
                # Lista (validar después en su sección)
                resultado[key] = value
            else:
                # Campo simple
                nuevo_valor = self.validar_campo_simple(key, value, path)
                if nuevo_valor is None and key != "":
                    # Check si es señal de quit
                    if not Confirm.ask("¿Realmente quieres salir?", default=False):
                        nuevo_valor = value
                    else:
                        return None
                resultado[key] = nuevo_valor

        return resultado

    def validar_lista(self, lista_data: List[Dict], nombre_seccion: str, singular: str) -> Optional[List]:
        """Valida una lista de items."""

        console.print(f"\n{'='*60}")
        console.print(f"  [bold cyan]VALIDANDO: {nombre_seccion} ({len(lista_data)} items)[/bold cyan]")
        console.print(f"{'='*60}\n")

        if len(lista_data) == 0:
            console.print("[dim]Lista vacía[/dim]")
            if Confirm.ask(f"¿Agregar un {singular}?", default=False):
                # TODO: Implementar agregar item
                console.print("[yellow]Funcionalidad de agregar pendiente[/yellow]")
            return lista_data

        resultado = []

        for i, item in enumerate(lista_data):
            console.print(f"\n[bold]──── {singular.upper()} {i+1}/{len(lista_data)} ────[/bold]\n")

            # Mostrar preview del item
            self.mostrar_item_preview(item)

            console.print("\n[V]alidar  [E]liminar  [S]kip  [Q]uit")
            accion = Prompt.ask("Acción", choices=["v", "e", "s", "q"], default="v").lower()

            if accion == "q":
                return None  # Quit signal
            elif accion == "e":
                if Confirm.ask(f"¿Confirmar eliminación de {singular} {i+1}?", default=False):
                    self.campos_eliminados += 1
                    continue  # No agregar a resultado
                else:
                    resultado.append(item)
            elif accion == "s":
                resultado.append(item)
            else:  # 'v'
                # Validar item completo
                item_validado = self.validar_dict(item, f"{singular} {i+1}", nombre_seccion)
                if item_validado is None:
                    return None  # Quit signal
                resultado.append(item_validado)

        # Opción de agregar más items
        if Confirm.ask(f"\n¿Agregar otro {singular}?", default=False):
            console.print("[yellow]Funcionalidad de agregar pendiente[/yellow]")

        return resultado

    def mostrar_item_preview(self, item: Dict):
        """Muestra preview de un item de lista."""
        table = Table(show_header=False, box=None)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")

        # Mostrar primeros 3-4 campos más importantes
        count = 0
        for key, value in item.items():
            if count >= 4:
                break
            if not isinstance(value, (dict, list)):
                val_str = str(value)[:50]
                if len(str(value)) > 50:
                    val_str += "..."
                table.add_row(key, val_str)
                count += 1

        console.print(table)

    def menu_principal(self) -> bool:
        """Muestra menú principal de navegación."""

        while True:
            console.clear()
            console.print(Panel.fit(
                "[bold cyan]VALIDACIÓN DE GROUND TRUTH[/bold cyan]\n"
                f"Archivo: {self.json_path.name}",
                border_style="cyan"
            ))

            # Contar items en cada sección
            n_diag = len(self.historia_dict.get('diagnosticos', []))
            n_ant = len(self.historia_dict.get('antecedentes', []))
            n_exam = len(self.historia_dict.get('examenes', []))
            n_incap = len(self.historia_dict.get('incapacidades', []))
            n_recom = len(self.historia_dict.get('recomendaciones', []))
            n_remis = len(self.historia_dict.get('remisiones', []))
            n_sve = len(self.historia_dict.get('programas_sve', []))

            menu_text = f"""
[bold]Secciones:[/bold]

 [1]  Metadata y datos del empleado
 [2]  EMO y signos vitales
 [3]  Diagnósticos ({n_diag} encontrados)
 [4]  Antecedentes ({n_ant} encontrados)
 [5]  Exámenes ({n_exam} encontrados)
 [6]  Incapacidades ({n_incap} encontradas)
 [7]  Recomendaciones ({n_recom} encontradas)
 [8]  Remisiones ({n_remis} encontradas)
 [9]  Aptitud y restricciones
[10]  Programas SVE ({n_sve} programas)

[bold cyan][S]  Guardar y salir[/bold cyan]
[bold red][Q]  Salir sin guardar[/bold red]
"""
            console.print(Panel(menu_text, border_style="blue"))

            # Stats actuales
            console.print(f"\n[dim]Editados: {self.campos_editados} | "
                         f"Eliminados: {self.campos_eliminados} | "
                         f"Agregados: {self.campos_agregados}[/dim]\n")

            opcion = Prompt.ask(
                "Selecciona sección",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "s", "q"],
                default="1"
            ).lower()

            if opcion == "q":
                if Confirm.ask("¿Salir sin guardar?", default=False):
                    return False
            elif opcion == "s":
                return True
            elif opcion == "1":
                self.validar_seccion_metadata()
            elif opcion == "2":
                self.validar_seccion_emo()
            elif opcion == "3":
                self.validar_seccion_diagnosticos()
            elif opcion == "4":
                self.validar_seccion_antecedentes()
            elif opcion == "5":
                self.validar_seccion_examenes()
            elif opcion == "6":
                self.validar_seccion_incapacidades()
            elif opcion == "7":
                self.validar_seccion_recomendaciones()
            elif opcion == "8":
                self.validar_seccion_remisiones()
            elif opcion == "9":
                self.validar_seccion_aptitud()
            elif opcion == "10":
                self.validar_seccion_sve()

    def validar_seccion_metadata(self):
        """Valida metadata y datos del empleado."""
        datos = {
            "archivo_origen": self.historia_dict.get('archivo_origen'),
            "tipo_documento_fuente": self.historia_dict.get('tipo_documento_fuente'),
            "datos_empleado": self.historia_dict.get('datos_empleado', {})
        }

        validado = self.validar_dict(datos, "Metadata y Datos del Empleado")
        if validado:
            self.historia_dict['archivo_origen'] = validado['archivo_origen']
            self.historia_dict['tipo_documento_fuente'] = validado['tipo_documento_fuente']
            self.historia_dict['datos_empleado'] = validado['datos_empleado']

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_emo(self):
        """Valida EMO y signos vitales."""
        datos = {
            "tipo_emo": self.historia_dict.get('tipo_emo'),
            "fecha_emo": self.historia_dict.get('fecha_emo'),
            "signos_vitales": self.historia_dict.get('signos_vitales', {}),
            "hallazgos_examen_fisico": self.historia_dict.get('hallazgos_examen_fisico')
        }

        validado = self.validar_dict(datos, "EMO y Signos Vitales")
        if validado:
            self.historia_dict['tipo_emo'] = validado['tipo_emo']
            self.historia_dict['fecha_emo'] = validado['fecha_emo']
            self.historia_dict['signos_vitales'] = validado['signos_vitales']
            self.historia_dict['hallazgos_examen_fisico'] = validado['hallazgos_examen_fisico']

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_diagnosticos(self):
        """Valida lista de diagnósticos."""
        diagnosticos = self.historia_dict.get('diagnosticos', [])
        validados = self.validar_lista(diagnosticos, "Diagnósticos", "diagnóstico")
        if validados is not None:
            self.historia_dict['diagnosticos'] = validados

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_antecedentes(self):
        """Valida lista de antecedentes."""
        antecedentes = self.historia_dict.get('antecedentes', [])
        validados = self.validar_lista(antecedentes, "Antecedentes", "antecedente")
        if validados is not None:
            self.historia_dict['antecedentes'] = validados

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_examenes(self):
        """Valida lista de exámenes."""
        examenes = self.historia_dict.get('examenes', [])
        validados = self.validar_lista(examenes, "Exámenes", "examen")
        if validados is not None:
            self.historia_dict['examenes'] = validados

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_incapacidades(self):
        """Valida lista de incapacidades."""
        incapacidades = self.historia_dict.get('incapacidades', [])
        validados = self.validar_lista(incapacidades, "Incapacidades", "incapacidad")
        if validados is not None:
            self.historia_dict['incapacidades'] = validados

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_recomendaciones(self):
        """Valida lista de recomendaciones."""
        recomendaciones = self.historia_dict.get('recomendaciones', [])
        validados = self.validar_lista(recomendaciones, "Recomendaciones", "recomendación")
        if validados is not None:
            self.historia_dict['recomendaciones'] = validados

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_remisiones(self):
        """Valida lista de remisiones."""
        remisiones = self.historia_dict.get('remisiones', [])
        validados = self.validar_lista(remisiones, "Remisiones", "remisión")
        if validados is not None:
            self.historia_dict['remisiones'] = validados

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_aptitud(self):
        """Valida aptitud y restricciones."""
        datos = {
            "aptitud_laboral": self.historia_dict.get('aptitud_laboral'),
            "restricciones_especificas": self.historia_dict.get('restricciones_especificas'),
            "genera_reincorporacion": self.historia_dict.get('genera_reincorporacion'),
            "causa_reincorporacion": self.historia_dict.get('causa_reincorporacion')
        }

        validado = self.validar_dict(datos, "Aptitud y Restricciones")
        if validado:
            self.historia_dict['aptitud_laboral'] = validado['aptitud_laboral']
            self.historia_dict['restricciones_especificas'] = validado['restricciones_especificas']
            self.historia_dict['genera_reincorporacion'] = validado['genera_reincorporacion']
            self.historia_dict['causa_reincorporacion'] = validado['causa_reincorporacion']

        Prompt.ask("\n[Presiona Enter para continuar]")

    def validar_seccion_sve(self):
        """Valida programas SVE."""
        sve = self.historia_dict.get('programas_sve', [])

        console.print(f"\n[bold cyan]Programas SVE ({len(sve)} programas)[/bold cyan]\n")

        if sve:
            for i, prog in enumerate(sve):
                console.print(f"  {i+1}. {prog}")
        else:
            console.print("[dim]No hay programas SVE[/dim]")

        if Confirm.ask("\n¿Editar programas SVE?", default=False):
            nuevos = Prompt.ask("Ingresa programas separados por coma", default=",".join(sve))
            self.historia_dict['programas_sve'] = [p.strip() for p in nuevos.split(',') if p.strip()]

        Prompt.ask("\n[Presiona Enter para continuar]")

    def guardar_validacion(self) -> bool:
        """Guarda el JSON validado y el reporte."""
        try:
            # Guardar JSON validado
            stem = self.json_path.stem
            validated_path = self.output_dir / f"{stem}_validated.json"

            with open(validated_path, 'w', encoding='utf-8') as f:
                json.dump(self.historia_dict, f, indent=2, ensure_ascii=False)

            # Guardar reporte de correcciones
            report_path = self.output_dir / f"{stem}_corrections_report.json"

            report = {
                "archivo_original": str(self.json_path),
                "fecha_validacion": datetime.now().isoformat(),
                "estadisticas": {
                    "campos_editados": self.campos_editados,
                    "campos_eliminados": self.campos_eliminados,
                    "campos_agregados": self.campos_agregados,
                    "total_correcciones": len(self.correcciones)
                },
                "correcciones": self.correcciones
            }

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            console.print(f"\n[green]✅ JSON validado: {validated_path}[/green]")
            console.print(f"[green]✅ Reporte: {report_path}[/green]")
            console.print(f"\n[cyan]Resumen:[/cyan]")
            console.print(f"  • Campos editados: {self.campos_editados}")
            console.print(f"  • Campos eliminados: {self.campos_eliminados}")
            console.print(f"  • Campos agregados: {self.campos_agregados}")
            console.print(f"  • Total correcciones: {len(self.correcciones)}")

            return True

        except Exception as e:
            console.print(f"[red]❌ Error guardando: {e}[/red]")
            return False


@click.command()
@click.argument('json_path', type=click.Path(exists=True))
@click.option(
    '--pdf-dir',
    type=click.Path(exists=True),
    default='data/raw',
    help='Directorio donde buscar los PDFs de origen (default: data/raw/)'
)
@click.option(
    '--output',
    '-o',
    type=click.Path(),
    default='data/labeled',
    help='Directorio de salida (default: data/labeled/)'
)
def main(json_path, pdf_dir, output):
    """
    Valida ground truth de una historia clínica COMPLETA (consolidada o individual).

    Auto-detecta y carga los PDFs de origen desde archivos_origen_consolidados.
    Navega por secciones validando TODO el JSON.
    Captura razones de cada corrección.

    Ejemplos:
        # JSON consolidado (auto-detecta múltiples PDFs)
        python validate_ground_truth_v2.py data/processed/12345678_consolidated.json

        # JSON individual (auto-detecta 1 PDF)
        python validate_ground_truth_v2.py data/processed/HC_001.json

        # Especificar directorio custom de PDFs
        python validate_ground_truth_v2.py consolidated.json --pdf-dir /path/to/pdfs/
    """
    console.print("\n[bold cyan]═══════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  VALIDADOR DE GROUND TRUTH v2.0 - COMPLETO[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════[/bold cyan]\n")

    session = ValidationSession(
        json_path=Path(json_path),
        pdf_dir=Path(pdf_dir),
        output_dir=Path(output)
    )

    # Cargar datos
    if not session.load_data():
        console.print("[red]❌ Error cargando datos[/red]")
        return

    # Mostrar info inicial
    console.print(f"[bold]Archivo:[/bold] {session.json_path.name}")
    console.print(f"[bold]Tipo documento:[/bold] {session.historia_dict.get('tipo_documento_fuente', 'N/A')}")
    console.print(f"[bold]PDFs cargados:[/bold] {len(session.pdfs_texto)}")
    for nombre in session.pdfs_texto.keys():
        console.print(f"  • {nombre}")
    console.print()

    Prompt.ask("[Presiona Enter para comenzar]")

    # Menú principal
    if session.menu_principal():
        # Guardar
        if session.guardar_validacion():
            console.print("\n[bold green]✅ Validación completada exitosamente[/bold green]\n")
        else:
            console.print("\n[bold red]❌ Error guardando validación[/bold red]\n")
    else:
        console.print("\n[yellow]⚠️  Validación cancelada[/yellow]\n")


if __name__ == '__main__':
    main()
