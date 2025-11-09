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

    # Verificar por campo_afectado
    campo = alerta.campo_afectado
    if campo == 'tipo_emo' and historia.tipo_emo is not None:
        return True
    if campo == 'aptitud_laboral' and historia.aptitud_laboral is not None:
        return True
    if campo == 'fecha_emo' and historia.fecha_emo is not None:
        return True
    if campo == 'diagnosticos' and len(historia.diagnosticos) > 0:
        return True

    # También verificar por descripción (alertas que mencionan estos campos)
    desc_lower = alerta.descripcion.lower()

    # Si alerta menciona tipo_emo pero el consolidado lo tiene
    if 'tipo_emo' in desc_lower or 'tipo de emo' in desc_lower:
        if historia.tipo_emo is not None:
            return True

    # Si alerta menciona aptitud pero el consolidado la tiene
    if 'aptitud' in desc_lower:
        if historia.aptitud_laboral is not None:
            return True

    # Si alerta menciona diagnósticos pero el consolidado los tiene
    if 'diagnostico' in desc_lower or 'diagnóstico' in desc_lower:
        if len(historia.diagnosticos) > 0:
            return True

    # Si alerta menciona fecha_emo pero el consolidado la tiene
    if 'fecha_emo' in desc_lower or 'fecha del emo' in desc_lower:
        if historia.fecha_emo is not None:
            return True

    return False


def is_invalid_for_exam_especifico(alerta, historia: HistoriaClinicaEstructurada) -> bool:
    """
    Verifica si una alerta no aplica a exámenes específicos.

    Exámenes específicos (laboratorio, optometría, audiometría, RX) NO requieren:
    - tipo_emo
    - aptitud_laboral
    - diagnóstico principal
    - fecha_emo (pueden tener fecha_realizacion del examen)

    Args:
        alerta: Objeto Alerta
        historia: Historia clínica procesada

    Returns:
        bool: True si no aplica a examen específico
    """
    # Solo aplica a exámenes específicos
    if historia.tipo_documento_fuente != "examen_especifico":
        return False

    # Solo filtrar alertas de dato_faltante en exámenes específicos
    if alerta.tipo != "dato_faltante":
        return False

    desc_lower = alerta.descripcion.lower()

    # Alertas que NO aplican a exámenes específicos:

    # 1. Diagnóstico principal
    if "diagnóstico principal" in desc_lower or "diagnostico principal" in desc_lower:
        return True

    # 2. Tipo de EMO (examen específico no es un EMO completo)
    if "tipo_emo" in desc_lower or "tipo de emo" in desc_lower or "sin tipo_emo" in desc_lower:
        return True

    # 3. Aptitud laboral (solo en HC completa/CMO)
    if "aptitud" in desc_lower and "laboral" in desc_lower:
        return True
    if "concepto de aptitud" in desc_lower or "sin aptitud" in desc_lower:
        return True

    # 4. Fecha EMO (examen tiene fecha_realizacion, no fecha_emo)
    if "fecha_emo" in desc_lower or "fecha del emo" in desc_lower:
        return True

    # 5. Diagnósticos faltantes (examen específico puede no tener diagnósticos)
    # Solo si la alerta dice "no se encontraron diagnósticos" genéricamente
    if "no se encontraron diagnosticos" in desc_lower or "no se encontraron diagnósticos" in desc_lower:
        return True
    if "sin diagnosticos" in desc_lower or "sin diagnósticos" in desc_lower:
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
