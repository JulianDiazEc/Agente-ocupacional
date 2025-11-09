#!/usr/bin/env python3
"""
Script para consolidar múltiples exámenes médicos de una misma persona.

Une HC base, RX, laboratorios, audiometrías, etc. en un único JSON
consolidado sin duplicados.

Uso:
    python consolidate_person.py --files HC_juan.json RX_juan.json Labs_juan.json
    python consolidate_person.py --pattern "data/processed/JUAN*"
    python consolidate_person.py --person "12345678" --dir data/processed/
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Imports para validaciones del consolidado
from src.config.schemas import HistoriaClinicaEstructurada
from src.processors.validators import validate_historia_completa
from src.processors.alert_filters import filter_alerts

console = Console()


def load_json_files(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """Carga múltiples archivos JSON."""
    historias = []
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                historias.append(data)
                console.print(f"✅ Cargado: {path.name}")
        except Exception as e:
            console.print(f"[red]❌ Error cargando {path.name}: {e}[/red]")
    return historias


def merge_diagnosticos(historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge inteligente de diagnósticos evitando duplicados.

    Consolida por código CIE-10. Si hay duplicados, mantiene el de mayor confianza.
    """
    diagnosticos_dict = {}

    for historia in historias:
        for diag in historia.get('diagnosticos', []):
            codigo = diag.get('codigo_cie10')
            if not codigo:
                continue

            # Si no existe, agregar
            if codigo not in diagnosticos_dict:
                diagnosticos_dict[codigo] = diag
            else:
                # Si existe, mantener el de mayor confianza
                confianza_actual = diagnosticos_dict[codigo].get('confianza', 0.0)
                confianza_nueva = diag.get('confianza', 0.0)

                if confianza_nueva > confianza_actual:
                    diagnosticos_dict[codigo] = diag

    return list(diagnosticos_dict.values())


def merge_antecedentes(historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge inteligente de antecedentes evitando duplicados.

    Consolida por tipo + descripción (normalizada).
    """
    antecedentes_dict = {}

    for historia in historias:
        for ant in historia.get('antecedentes', []):
            tipo = ant.get('tipo', '')
            descripcion = ant.get('descripcion', '').strip().lower()

            if not descripcion:
                continue

            # Clave única: tipo + descripción normalizada
            key = f"{tipo}:{descripcion}"

            # Si no existe, agregar
            if key not in antecedentes_dict:
                antecedentes_dict[key] = ant
            else:
                # Si existe, actualizar fecha si es más reciente
                fecha_actual = antecedentes_dict[key].get('fecha_aproximada', '')
                fecha_nueva = ant.get('fecha_aproximada', '')

                if fecha_nueva and (not fecha_actual or fecha_nueva > fecha_actual):
                    antecedentes_dict[key] = ant

    return list(antecedentes_dict.values())


def merge_examenes(historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge inteligente de exámenes evitando duplicados.

    Consolida por tipo + fecha. Mantiene orden cronológico.
    """
    examenes_dict = {}

    for historia in historias:
        for exam in historia.get('examenes', []):
            tipo = exam.get('tipo', '')
            fecha = exam.get('fecha_realizacion', '')

            if not tipo:
                continue

            # Clave única: tipo + fecha
            key = f"{tipo}:{fecha}"

            # Agregar o sobrescribir (última versión gana)
            examenes_dict[key] = exam

    # Ordenar por fecha (más recientes primero)
    examenes_list = list(examenes_dict.values())
    examenes_list.sort(
        key=lambda x: x.get('fecha_realizacion', ''),
        reverse=True
    )

    return examenes_list


def merge_incapacidades(historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge de incapacidades sin duplicados.

    Consolida por fecha_inicio + tipo.
    """
    incapacidades_dict = {}

    for historia in historias:
        for incap in historia.get('incapacidades', []):
            fecha_inicio = incap.get('fecha_inicio', '')
            tipo = incap.get('tipo', '')

            if not fecha_inicio:
                continue

            key = f"{fecha_inicio}:{tipo}"
            incapacidades_dict[key] = incap

    # Ordenar por fecha_inicio (más recientes primero)
    incapacidades_list = list(incapacidades_dict.values())
    incapacidades_list.sort(
        key=lambda x: x.get('fecha_inicio', ''),
        reverse=True
    )

    return incapacidades_list


def merge_recomendaciones(historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge inteligente de recomendaciones evitando duplicados.

    Consolida por tipo + descripción normalizada.
    """
    recomendaciones_dict = {}

    for historia in historias:
        for rec in historia.get('recomendaciones', []):
            tipo = rec.get('tipo', '')
            descripcion = rec.get('descripcion', '').strip().lower()

            if not descripcion:
                continue

            key = f"{tipo}:{descripcion}"

            # Si no existe, agregar
            if key not in recomendaciones_dict:
                recomendaciones_dict[key] = rec
            else:
                # Si existe, mantener la de mayor prioridad
                prioridades = {'alta': 3, 'media': 2, 'baja': 1}
                prioridad_actual = prioridades.get(
                    recomendaciones_dict[key].get('prioridad', 'media'), 2
                )
                prioridad_nueva = prioridades.get(
                    rec.get('prioridad', 'media'), 2
                )

                if prioridad_nueva > prioridad_actual:
                    recomendaciones_dict[key] = rec

    return list(recomendaciones_dict.values())


def merge_remisiones(historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge de remisiones evitando duplicados.

    Consolida por especialidad + motivo.
    """
    remisiones_dict = {}

    for historia in historias:
        for rem in historia.get('remisiones', []):
            especialidad = rem.get('especialidad', '').strip().lower()
            motivo = rem.get('motivo', '').strip().lower()

            if not especialidad:
                continue

            key = f"{especialidad}:{motivo}"

            # Agregar o actualizar fecha si es más reciente
            if key not in remisiones_dict:
                remisiones_dict[key] = rem
            else:
                fecha_actual = remisiones_dict[key].get('fecha_planeada', '')
                fecha_nueva = rem.get('fecha_planeada', '')

                if fecha_nueva and (not fecha_actual or fecha_nueva > fecha_actual):
                    remisiones_dict[key] = rem

    return list(remisiones_dict.values())


def merge_alertas(historias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    [DEPRECATED] Ya no se usa - Las alertas se generan solo sobre el consolidado final.

    Anteriormente hacía merge de alertas de documentos individuales,
    pero esto generaba ruido (alertas de exámenes específicos que no aplican).

    Ahora las alertas se ejecutan SOLO sobre el consolidado final con lista blanca clínica.
    """
    # Esta función ya no se llama, pero se mantiene por compatibilidad
    return []


def consolidate_historias(historias: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Consolida múltiples historias clínicas en una sola.

    Prioriza datos de HC completa/CMO sobre exámenes específicos para campos generales.

    Args:
        historias: Lista de historias clínicas a consolidar

    Returns:
        Historia clínica consolidada
    """
    if not historias:
        raise ValueError("No hay historias para consolidar")

    # Separar HC completas/CMO de exámenes específicos
    hcs_completas = [h for h in historias if h.get('tipo_documento_fuente') in ['hc_completa', 'cmo']]
    examenes_especificos = [h for h in historias if h.get('tipo_documento_fuente') == 'examen_especifico']

    # Usar HC completa como base si existe, sino la primera
    if hcs_completas:
        consolidada = hcs_completas[0].copy()
        # Tipo documento del consolidado
        consolidada['tipo_documento_fuente'] = 'hc_completa'
    else:
        consolidada = historias[0].copy()

    # Merge de datos del empleado - PRIORIZAR HC COMPLETA
    datos_empleado = {}

    # Primero tomar de exámenes específicos (datos básicos)
    for historia in examenes_especificos:
        empleado = historia.get('datos_empleado', {})
        for key, value in empleado.items():
            if value is not None and value != "" and value != "Empleado":
                datos_empleado[key] = value

    # Luego sobrescribir con datos de HC completas (más confiables)
    for historia in hcs_completas:
        empleado = historia.get('datos_empleado', {})
        for key, value in empleado.items():
            if value is not None and value != "" and value != "Empleado":
                # Priorizar cargo específico sobre "Empleado" genérico
                if key == 'cargo':
                    if value and value.lower() not in ['empleado', 'trabajador', 'personal']:
                        datos_empleado[key] = value
                else:
                    datos_empleado[key] = value

    consolidada['datos_empleado'] = datos_empleado

    # Merge de signos vitales - PRIORIZAR HC COMPLETA
    signos_vitales = None
    for historia in reversed(hcs_completas):  # Más reciente primero
        sv = historia.get('signos_vitales')
        if sv:
            signos_vitales = sv
            break

    # Si no hay en HC, tomar de exámenes (poco probable pero posible)
    if not signos_vitales:
        for historia in reversed(examenes_especificos):
            sv = historia.get('signos_vitales')
            if sv:
                signos_vitales = sv
                break

    consolidada['signos_vitales'] = signos_vitales

    # Tipo EMO y fecha - PRIORIZAR HC COMPLETA
    tipo_emo_encontrado = False
    for historia in hcs_completas:
        if historia.get('tipo_emo'):
            consolidada['tipo_emo'] = historia['tipo_emo']
            tipo_emo_encontrado = True
            break

    # Fecha EMO de HC completa
    fecha_emo_encontrada = False
    for historia in hcs_completas:
        if historia.get('fecha_emo'):
            consolidada['fecha_emo'] = historia['fecha_emo']
            fecha_emo_encontrada = True
            break

    # Merge inteligente de campos con lógica de deduplicación
    consolidada['diagnosticos'] = merge_diagnosticos(historias)
    consolidada['antecedentes'] = merge_antecedentes(historias)
    consolidada['examenes'] = merge_examenes(historias)
    consolidada['incapacidades'] = merge_incapacidades(historias)
    consolidada['recomendaciones'] = merge_recomendaciones(historias)
    consolidada['remisiones'] = merge_remisiones(historias)

    # IMPORTANTE: NO heredar alertas de documentos individuales
    # Las alertas se generarán solo sobre el consolidado final
    consolidada['alertas_validacion'] = []

    # Aptitud laboral - PRIORIZAR HC COMPLETA/CMO (no exámenes específicos)
    aptitud_encontrada = False
    for historia in reversed(hcs_completas):  # Más reciente primero
        if historia.get('aptitud_laboral'):
            consolidada['aptitud_laboral'] = historia['aptitud_laboral']
            consolidada['restricciones_especificas'] = historia.get('restricciones_especificas')
            consolidada['genera_reincorporacion'] = historia.get('genera_reincorporacion', False)
            consolidada['causa_reincorporacion'] = historia.get('causa_reincorporacion')
            aptitud_encontrada = True
            break

    # Si no hay aptitud en HC completas, tomar de cualquier fuente (fallback)
    if not aptitud_encontrada:
        for historia in reversed(historias):
            if historia.get('aptitud_laboral'):
                consolidada['aptitud_laboral'] = historia['aptitud_laboral']
                consolidada['restricciones_especificas'] = historia.get('restricciones_especificas')
                consolidada['genera_reincorporacion'] = historia.get('genera_reincorporacion', False)
                consolidada['causa_reincorporacion'] = historia.get('causa_reincorporacion')
                break

    # Programas SVE: unión de todos
    sve_set = set()
    for historia in historias:
        sve_set.update(historia.get('programas_sve', []))
    consolidada['programas_sve'] = sorted(list(sve_set))

    # Metadata de consolidación
    consolidada['archivos_origen_consolidados'] = [
        h.get('archivo_origen', 'desconocido') for h in historias
    ]
    consolidada['fecha_consolidacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    consolidada['total_documentos_consolidados'] = len(historias)

    # Recalcular confianza promedio
    confianzas = []
    for diag in consolidada.get('diagnosticos', []):
        confianzas.append(diag.get('confianza', 0.0))

    if confianzas:
        consolidada['confianza_extraccion'] = sum(confianzas) / len(confianzas)

    # Agregar nota de procesamiento
    nota = f"Consolidado de {len(historias)} documentos: {', '.join([Path(h.get('archivo_origen', '')).stem for h in historias])}"
    consolidada['notas_procesamiento'] = nota

    # VALIDACIONES DEL CONSOLIDADO FINAL
    # Solo aquí se ejecutan validaciones de completitud y consistencia
    # NO se heredan alertas de documentos individuales
    try:
        # Setear tipo de documento como consolidado
        consolidada['tipo_documento_fuente'] = 'consolidado'

        # Convertir a objeto Pydantic para validar
        historia_obj = HistoriaClinicaEstructurada.model_validate(consolidada)

        # Ejecutar validaciones de completitud
        alertas_validacion = validate_historia_completa(historia_obj)

        # Filtrar con lista blanca clínica
        alertas_filtradas = filter_alerts(alertas_validacion, historia_obj)

        # Actualizar alertas en el dict
        consolidada['alertas_validacion'] = [
            {
                'tipo': alerta.tipo,
                'severidad': alerta.severidad,
                'campo_afectado': alerta.campo_afectado,
                'descripcion': alerta.descripcion,
                'accion_sugerida': alerta.accion_sugerida
            }
            for alerta in alertas_filtradas
        ]

        console.print(f"   ✅ Validaciones ejecutadas: {len(alertas_filtradas)} alertas clínicas")

    except Exception as e:
        console.print(f"   [yellow]⚠️ Error en validaciones: {e}[/yellow]")
        # Si falla validación, dejar alertas vacías (ya están en [])

    return consolidada


def print_summary(consolidada: Dict[str, Any]) -> None:
    """Imprime resumen de la consolidación."""

    console.print("\n")
    console.print(Panel.fit(
        "[bold green]✅ CONSOLIDACIÓN COMPLETADA[/bold green]",
        border_style="green"
    ))

    # Tabla de resumen
    table = Table(title="📊 Resumen de Consolidación", show_header=True)
    table.add_column("Campo", style="cyan", width=30)
    table.add_column("Cantidad", justify="right", style="yellow")

    table.add_row("Documentos consolidados", str(consolidada.get('total_documentos_consolidados', 0)))
    table.add_row("Diagnósticos únicos", str(len(consolidada.get('diagnosticos', []))))
    table.add_row("Antecedentes únicos", str(len(consolidada.get('antecedentes', []))))
    table.add_row("Exámenes", str(len(consolidada.get('examenes', []))))
    table.add_row("Incapacidades", str(len(consolidada.get('incapacidades', []))))
    table.add_row("Recomendaciones únicas", str(len(consolidada.get('recomendaciones', []))))
    table.add_row("Remisiones únicas", str(len(consolidada.get('remisiones', []))))
    table.add_row("Programas SVE", str(len(consolidada.get('programas_sve', []))))
    table.add_row("Alertas", str(len(consolidada.get('alertas_validacion', []))))

    console.print(table)

    # Información del empleado
    empleado = consolidada.get('datos_empleado', {})
    if empleado:
        console.print(f"\n👤 [bold]Empleado:[/bold] {empleado.get('nombre_completo', 'N/A')}")
        console.print(f"📄 [bold]Documento:[/bold] {empleado.get('documento', 'N/A')}")
        console.print(f"💼 [bold]Cargo:[/bold] {empleado.get('cargo', 'N/A')}")

    # Aptitud laboral
    aptitud = consolidada.get('aptitud_laboral')
    if aptitud:
        color = "green" if aptitud == "apto" else "yellow" if "restricciones" in aptitud else "red"
        console.print(f"\n✅ [bold {color}]Aptitud Laboral:[/bold {color}] {aptitud}")

    # Archivos consolidados
    console.print(f"\n📁 [bold]Archivos consolidados:[/bold]")
    for archivo in consolidada.get('archivos_origen_consolidados', []):
        console.print(f"   • {archivo}")


@click.command()
@click.option(
    '--files',
    '-f',
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    help='Archivos JSON a consolidar'
)
@click.option(
    '--pattern',
    '-p',
    type=str,
    help='Patrón glob para buscar archivos (ej: "data/processed/JUAN*")'
)
@click.option(
    '--person',
    type=str,
    help='Número de documento de la persona (busca archivos que lo contengan)'
)
@click.option(
    '--dir',
    '-d',
    type=click.Path(exists=True, path_type=Path),
    default=Path('data/processed'),
    help='Directorio donde buscar archivos (con --person o --pattern)'
)
@click.option(
    '--output',
    '-o',
    type=click.Path(path_type=Path),
    help='Archivo de salida (default: data/processed/{documento}_consolidated.json)'
)
def main(files, pattern, person, dir, output):
    """
    Consolida múltiples exámenes médicos de una misma persona en un único JSON.

    Ejemplos:

        # Por archivos específicos
        python consolidate_person.py -f HC_juan.json -f RX_juan.json -f Labs_juan.json

        # Por patrón
        python consolidate_person.py --pattern "data/processed/JUAN*"

        # Por documento
        python consolidate_person.py --person "12345678"
    """
    console.print("\n[bold cyan]🔄 CONSOLIDADOR DE HISTORIAS CLÍNICAS[/bold cyan]\n")

    # Determinar archivos a procesar
    file_paths = []

    if files:
        file_paths = list(files)
    elif pattern:
        file_paths = list(Path('.').glob(pattern))
    elif person:
        # Buscar archivos que contengan el documento en el nombre o contenido
        for json_file in dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    documento = data.get('datos_empleado', {}).get('documento', '')
                    if person in str(documento) or person in json_file.name:
                        file_paths.append(json_file)
            except:
                continue
    else:
        console.print("[red]❌ Debes especificar --files, --pattern o --person[/red]")
        return

    if not file_paths:
        console.print("[red]❌ No se encontraron archivos para consolidar[/red]")
        return

    console.print(f"📂 Encontrados {len(file_paths)} archivo(s)\n")

    # Cargar archivos
    historias = load_json_files(file_paths)

    if len(historias) < 2:
        console.print("\n[yellow]⚠️ Se necesitan al menos 2 archivos para consolidar[/yellow]")
        return

    console.print(f"\n🔄 Consolidando {len(historias)} historias clínicas...\n")

    # Consolidar
    try:
        consolidada = consolidate_historias(historias)
    except Exception as e:
        console.print(f"[red]❌ Error en consolidación: {e}[/red]")
        raise

    # Determinar archivo de salida
    if not output:
        documento = consolidada.get('datos_empleado', {}).get('documento', 'unknown')
        output = Path('data/processed') / f"{documento}_consolidated.json"

    # Guardar resultado
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(consolidada, f, indent=2, ensure_ascii=False)

    # Mostrar resumen
    print_summary(consolidada)

    console.print(f"\n💾 [bold green]Guardado en:[/bold green] {output}")
    console.print()


if __name__ == '__main__':
    main()
