"""
Filtrado centralizado de alertas.

Reglas simples:
1. Administrativa → filtrar siempre
2. Redundante en consolidado → filtrar si campo ya existe

NUNCA filtrar: inconsistencias clínicas reales (CIE inválido, fechas imposibles)
"""

from typing import List

from src.config.schemas import HistoriaClinicaEstructurada
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# LISTAS DE KEYWORDS
# ============================================================================

# Campos administrativos que NO son clínicamente críticos
ADMINISTRATIVE_KEYWORDS = [
    'eps', 'arl', 'afiliacion',
    'empresa', 'area', 'cargo', 'antiguedad',
    'edad', 'sexo', 'fecha_nacimiento'
]

# Tipos de alerta que NUNCA se filtran (críticas clínicas)
CRITICAL_ALERT_TYPES = [
    'inconsistencia_diagnostica',
    'fecha_invalida',
    'restriccion_sin_aptitud'
]


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def is_administrative_alert(alerta) -> bool:
    """
    Verifica si una alerta es de tipo administrativa.

    Args:
        alerta: Objeto Alerta

    Returns:
        bool: True si es administrativa
    """
    if alerta.tipo != "dato_faltante":
        return False

    desc_lower = alerta.descripcion.lower()
    campo_lower = (alerta.campo_afectado or "").lower()

    # Verificar si contiene keyword administrativa
    for keyword in ADMINISTRATIVE_KEYWORDS:
        if keyword in desc_lower or keyword in campo_lower:
            return True

    return False


def is_covered_in_consolidated(alerta, historia: HistoriaClinicaEstructurada) -> bool:
    """
    Verifica si una alerta está cubierta en un consolidado.

    Args:
        alerta: Objeto Alerta
        historia: Historia clínica procesada

    Returns:
        bool: True si está cubierta en el consolidado
    """
    # Verificar si es consolidado
    es_consolidado = hasattr(historia, 'archivos_origen_consolidados') and \
                     bool(getattr(historia, 'archivos_origen_consolidados', None))

    if not es_consolidado:
        return False

    if alerta.tipo != "dato_faltante":
        return False

    campo = alerta.campo_afectado

    # Verificar campos clínicos críticos
    if campo == 'tipo_emo' and historia.tipo_emo is not None:
        return True
    if campo == 'aptitud_laboral' and historia.aptitud_laboral is not None:
        return True
    if campo == 'fecha_emo' and historia.fecha_emo is not None:
        return True
    if campo == 'diagnosticos' and len(historia.diagnosticos) > 0:
        return True

    return False


def is_invalid_for_exam_especifico(alerta, historia: HistoriaClinicaEstructurada) -> bool:
    """
    Verifica si una alerta no aplica a exámenes específicos.

    Args:
        alerta: Objeto Alerta
        historia: Historia clínica procesada

    Returns:
        bool: True si no aplica a examen específico
    """
    # Solo aplica a exámenes específicos
    if historia.tipo_documento_fuente != "examen_especifico":
        return False

    # Alerta de diagnóstico principal NO aplica a exámenes específicos
    if "diagnóstico principal" in alerta.descripcion.lower():
        return True

    return False


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def filter_alerts(alertas: List, historia: HistoriaClinicaEstructurada) -> List:
    """
    Filtra alertas conservando solo las clínicamente relevantes.

    Reglas:
    1. Administrativa → filtrar siempre
    2. Redundante en consolidado → filtrar si campo ya existe
    3. Diagnóstico principal en examen específico → filtrar

    NUNCA filtrar: inconsistencias clínicas (CIE inválido, fechas imposibles)

    Args:
        alertas: Lista de alertas
        historia: Historia clínica procesada

    Returns:
        list: Alertas relevantes (filtradas)
    """
    if not alertas:
        return []

    filtered = []

    for alerta in alertas:
        should_filter = False
        razon_filtrado = ""

        # EXCEPCIÓN: NUNCA filtrar alertas críticas
        if alerta.tipo in CRITICAL_ALERT_TYPES:
            filtered.append(alerta)
            continue

        # REGLA 1: Filtrar administrativas
        if is_administrative_alert(alerta):
            should_filter = True
            razon_filtrado = "administrativa"

        # REGLA 2: Filtrar si cubierta en consolidado
        if not should_filter and is_covered_in_consolidated(alerta, historia):
            should_filter = True
            razon_filtrado = "cubierta en consolidado"

        # REGLA 3: Filtrar diagnóstico principal en examen específico
        if not should_filter and is_invalid_for_exam_especifico(alerta, historia):
            should_filter = True
            razon_filtrado = "diagnóstico principal en examen específico"

        # Aplicar decisión
        if should_filter:
            logger.debug(
                f"Alerta filtrada ({razon_filtrado}): '{alerta.descripcion[:60]}...'"
            )
        else:
            filtered.append(alerta)

    logger.info(
        f"Filtrado de alertas: {len(alertas)} → {len(filtered)} "
        f"({len(alertas) - len(filtered)} administrativas/redundantes eliminadas)"
    )

    return filtered


__all__ = ['filter_alerts']
