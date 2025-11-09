"""
Filtrado centralizado de alertas.

Enfoque: LISTA BLANCA de tipos de alerta + filtros específicos

CONSERVAR SIEMPRE:
- valor_critico
- formato_incorrecto
- inconsistencia_diagnostica
- fecha_invalida

FILTRAR:
- dato_faltante administrativo (eps, arl, empresa, cargo, area, edad, sexo, etc.)
- dato_faltante redundante en consolidados (campo ya existe)
- dato_faltante inválido para examen_especifico (tipo_emo, aptitud, diagnósticos)
- evaluacion_incompleta (ruido)
"""

import re
from typing import List

from src.config.schemas import HistoriaClinicaEstructurada
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# LISTA BLANCA: Tipos de alerta que SIEMPRE se conservan
WHITELIST_ALERT_TYPES = {
    'valor_critico',
    'formato_incorrecto',
    'inconsistencia_diagnostica',
    'fecha_invalida'
}

# Campos administrativos (usar regex con word boundaries)
ADMINISTRATIVE_FIELDS_PATTERN = re.compile(
    r'\b(eps|arl|afiliacion|empresa|area|cargo|antiguedad|edad|sexo|fecha_nacimiento)\b',
    re.IGNORECASE
)


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def is_signos_vitales_alert_in_cmo(alerta, historia: HistoriaClinicaEstructurada) -> bool:
    """
    Verifica si alerta de signos_vitales debe filtrarse en CMO.

    Un CMO (Certificado Médico Ocupacional) puede no tener signos vitales detallados.
    Solo debe conservar aptitud laboral y diagnósticos.

    Args:
        alerta: Objeto Alerta
        historia: Historia clínica procesada

    Returns:
        bool: True si debe filtrarse (es alerta de signos en CMO)
    """
    if historia.tipo_documento_fuente != "cmo":
        return False

    if alerta.tipo != "dato_faltante":
        return False

    desc_lower = alerta.descripcion.lower()
    campo = (alerta.campo_afectado or "").lower()

    # Filtrar alertas sobre signos vitales en CMO
    signos_keywords = ['signos_vitales', 'signos vitales', 'presion', 'frecuencia', 'temperatura', 'saturacion', 'peso', 'talla', 'imc']

    if any(kw in desc_lower or kw in campo for kw in signos_keywords):
        return True

    return False


def is_administrative_alert(alerta) -> bool:
    """
    Verifica si una alerta menciona campos administrativos.

    Usa regex con word boundaries para evitar falsos positivos.

    Args:
        alerta: Objeto Alerta

    Returns:
        bool: True si es administrativa
    """
    if alerta.tipo != "dato_faltante":
        return False

    desc = alerta.descripcion or ""
    campo = alerta.campo_afectado or ""

    # Buscar con word boundaries en descripción o campo_afectado
    if ADMINISTRATIVE_FIELDS_PATTERN.search(desc) or ADMINISTRATIVE_FIELDS_PATTERN.search(campo):
        return True

    return False


def is_covered_in_consolidated(alerta, historia: HistoriaClinicaEstructurada) -> bool:
    """
    Verifica si alerta de dato_faltante está cubierta en consolidado.

    Si el consolidado tiene el campo poblado, filtrar alertas de exámenes específicos
    que reportaban que faltaba ese campo.

    Args:
        alerta: Objeto Alerta
        historia: Historia clínica procesada

    Returns:
        bool: True si está cubierta en el consolidado
    """
    # Solo aplica a consolidados o HC completas
    if historia.tipo_documento_fuente not in ["consolidado", "hc_completa"]:
        return False

    if alerta.tipo != "dato_faltante":
        return False

    desc_lower = alerta.descripcion.lower()

    # Mapeo: palabra clave → campo a verificar
    field_checks = [
        (['tipo_emo', 'tipo de emo'], historia.tipo_emo),
        (['aptitud', 'aptitud laboral'], historia.aptitud_laboral),
        (['diagnostico', 'diagnóstico'], len(historia.diagnosticos) > 0),
        (['fecha_emo', 'fecha del emo'], historia.fecha_emo),
        (['signos vitales', 'signos_vitales'], historia.signos_vitales),
    ]

    for keywords, field_value in field_checks:
        # Si alerta menciona keyword Y campo existe → filtrar
        if any(kw in desc_lower for kw in keywords):
            if field_value:
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
    Filtra alertas usando LISTA BLANCA de tipos permitidos.

    CONSERVAR SIEMPRE (lista blanca):
    - valor_critico
    - formato_incorrecto
    - inconsistencia_diagnostica
    - fecha_invalida

    FILTRAR:
    - dato_faltante de signos_vitales en CMO (no requeridos)
    - dato_faltante administrativo (eps, arl, empresa, cargo, etc.)
    - dato_faltante redundante en consolidados (campo ya existe)
    - dato_faltante inválido para examen_especifico (tipo_emo, aptitud, etc.)
    - evaluacion_incompleta (ruido)

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

        # PRIMERO: LISTA BLANCA - Si tipo está en whitelist → conservar SIEMPRE
        if alerta.tipo in WHITELIST_ALERT_TYPES:
            filtered.append(alerta)
            continue

        # Si no está en lista blanca, evaluar filtros para dato_faltante y evaluacion_incompleta

        # REGLA 1: Filtrar evaluacion_incompleta (ruido)
        if alerta.tipo == "evaluacion_incompleta":
            should_filter = True
            razon_filtrado = "evaluacion_incompleta (ruido)"

        # REGLA 2: Filtrar signos_vitales en CMO
        if not should_filter and is_signos_vitales_alert_in_cmo(alerta, historia):
            should_filter = True
            razon_filtrado = "signos_vitales en CMO (no requeridos)"

        # REGLA 3: Filtrar dato_faltante administrativo
        if not should_filter and is_administrative_alert(alerta):
            should_filter = True
            razon_filtrado = "administrativa"

        # REGLA 4: Filtrar dato_faltante si cubierta en consolidado
        if not should_filter and is_covered_in_consolidated(alerta, historia):
            should_filter = True
            razon_filtrado = "cubierta en consolidado"

        # REGLA 5: Filtrar dato_faltante inválido para examen específico
        if not should_filter and is_invalid_for_exam_especifico(alerta, historia):
            should_filter = True
            razon_filtrado = "inválida para examen específico"

        # Aplicar decisión
        if should_filter:
            logger.debug(
                f"Alerta filtrada ({razon_filtrado}): '{alerta.descripcion[:60]}...'"
            )
        else:
            # No está en whitelist pero tampoco se filtró → conservar
            filtered.append(alerta)

    logger.info(
        f"Filtrado de alertas: {len(alertas)} → {len(filtered)} "
        f"({len(alertas) - len(filtered)} filtradas)"
    )

    return filtered


__all__ = ['filter_alerts']
