"""
Filtrado centralizado de recomendaciones.

Reglas simples:
1. Nombre suelto de examen (≤3 palabras + es examen conocido)
2. Genérico sin contexto (frase plantilla sin hallazgo/riesgo/parámetro)
3. Educacional/admin genérico

EXCEPCIÓN: Si tiene contexto clínico → conservar siempre
"""

import re
import unicodedata
from typing import Dict, List

from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# LISTAS DE PATRONES
# ============================================================================

# Nombres de exámenes médicos (no deben aparecer como recomendaciones sueltas)
EXAM_NAME_TERMS = [
    'espirometria', 'audiometria', 'optometria', 'visiometria',
    'laboratorio', 'laboratorios', 'radiografia', 'ecografia',
    'electrocardiograma', 'ecg', 'ekg', 'rayos x', 'rx',
    'tomografia', 'resonancia', 'parcial de orina', 'hemograma',
    'glicemia', 'colesterol', 'trigliceridos', 'cuadro hematico',
    'coprologico', 'vdrl', 'vih', 'hepatitis',
    'control periodico', 'control ocupacional', 'control anual'
]

# Patrones genéricos sin contexto (regex)
GENERIC_PATTERNS = [
    # EPP genérico
    r'uso\s+(adecuado|correcto)\s+de\s+(epp|elementos)',
    r'uso\s+de\s+proteccion\s+personal',
    r'elementos\s+de\s+proteccion\s+personal',

    # Educación/capacitación genérica
    r'educacion\s+en\s+(higiene|postura|autocuidado|estilos)',
    r'capacitacion\s+en\s+(autocuidado|estilos|habitos)',

    # Hábitos genéricos
    r'habitos\s+saludables',
    r'estilo\s+de\s+vida\s+saludable',
    r'mantener\s+habitos',

    # Fórmulas administrativas
    r'adherir\s+(lineamientos|guia|protocolo)',
    r'seguir\s+(lineamientos|guia|protocolo)',
    r'control\s+segun\s+(pve|programa)',
    r'lineamientos\s+del\s+ministerio',

    # Medidas genéricas sin parámetro
    r'\breposo\s+auditivo\b(?!.*\d+\s*(min|hora|hr))',  # reposo sin duración
    r'\bejercicio\s+fisico\b(?!.*\d+\s*(min|veces|sesiones))',  # ejercicio sin frecuencia
    r'\bfotoproteccion\b(?!.*fps|factor|exposicion)',  # fotoprotección sin contexto
    r'\buso\s+de\s+filtro\s+solar\b(?!.*fps|exposicion)',  # filtro solar sin contexto

    # Ejercicio/actividad genérica
    r'150\s+minutos.*ejercicio',  # Frase OMS genérica
    r'actividad\s+fisica\s+regular(?!.*\d+)',  # actividad sin parámetro

    # Pausas genéricas
    r'pausas\s+activas(?!.*cada|\d+)',
    r'pausas\s+laborales(?!.*cada|\d+)',

    # Postura genérica
    r'buena\s+postura(?!.*por|debido)',
    r'higiene\s+postural(?!.*por|debido)',

    # Hidratación genérica
    r'\bhidratacion\b(?!.*\d+\s*(litros|ml))',
    r'consumo\s+de\s+agua(?!.*\d+)',
]


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normaliza texto: lowercase, sin tildes, sin dobles espacios.

    Args:
        text: Texto a normalizar

    Returns:
        str: Texto normalizado
    """
    text = text.lower().strip()
    # Remover tildes
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Remover dobles espacios
    text = ' '.join(text.split())
    return text


def has_clinical_context(descripcion: str) -> bool:
    """
    Verifica si la recomendación tiene contexto clínico específico.

    Contexto clínico = contiene al menos UNO de:
    - Números con unidades: 85 dB, 15 kg, 120/80 mmHg
    - Frecuencias: cada 6 meses, anual, semanal
    - Causales: por exposición, por diagnóstico, debido a
    - Parámetros: >, <, =
    - Condiciones específicas

    Args:
        descripcion: Texto de la recomendación

    Returns:
        bool: True si tiene contexto clínico
    """
    desc_lower = descripcion.lower()

    # Indicadores de contexto clínico
    clinical_indicators = [
        # Números con unidades
        r'\d+\s*(mg|db|kg|mmhg|cm|mm|metros|°|grados|fps|hz)',

        # Frecuencias temporales
        r'cada\s+\d+',
        r'\d+\s*(veces|sesiones)',
        r'\b(anual|mensual|semanal|diario|trimestral|semestral)\b',

        # Causales clínicos
        r'por\s+(exposicion|diagnostico|hallazgo|riesgo|antecedente)',
        r'debido\s+a',
        r'relacionado\s+con',

        # Parámetros y condiciones
        r'(>|<|=|mayor|menor|superior|inferior)\s*\d+',
        r'\bimc\s*(>|<|=)',
        r'nivel\s+de\s+\d+',

        # Códigos médicos
        r'\b[A-Z]\d{2}\.\d\b',  # CIE-10

        # Especificidad de puesto/área
        r'puesto\s+de',
        r'cargo\s+de',
        r'en\s+el\s+area\s+de',

        # Condiciones específicas
        r'si\s+\w+\s+(>|<|=)',
        r'en\s+caso\s+de\s+\w+\s+(>|<)',
    ]

    for pattern in clinical_indicators:
        if re.search(pattern, desc_lower):
            return True

    return False


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def filter_recommendations(recomendaciones: List[Dict], historia_dict: Dict) -> List[Dict]:
    """
    Filtra recomendaciones genéricas conservando solo las específicas.

    Reglas:
    1. Nombre suelto de examen (≤3 palabras) → filtrar
    2. Genérico sin contexto clínico → filtrar
    3. Educacional/admin genérico → filtrar

    EXCEPCIÓN: Si tiene contexto clínico → conservar siempre

    Args:
        recomendaciones: Lista de recomendaciones extraídas
        historia_dict: Diccionario de historia clínica (para contexto)

    Returns:
        list[dict]: Recomendaciones específicas (filtradas)
    """
    if not recomendaciones:
        return []

    filtered = []

    for rec in recomendaciones:
        descripcion = rec.get('descripcion', '')
        if not descripcion:
            continue

        desc_normalized = normalize_text(descripcion)
        palabra_count = len(descripcion.split())

        # PRIMERO: Verificar si tiene contexto clínico
        # Si tiene contexto → conservar SIEMPRE (excepción a todas las reglas)
        tiene_contexto = has_clinical_context(descripcion)

        if tiene_contexto:
            filtered.append(rec)
            logger.debug(f"Recomendación conservada (contexto clínico): '{descripcion[:60]}...'")
            continue

        # REGLA 1: Nombre suelto de examen (≤3 palabras + es examen conocido)
        is_exam_name = False
        if palabra_count <= 3:
            for exam_term in EXAM_NAME_TERMS:
                if exam_term in desc_normalized:
                    is_exam_name = True
                    logger.debug(
                        f"Recomendación filtrada (nombre suelto de examen): '{descripcion}'"
                    )
                    break

        if is_exam_name:
            continue

        # REGLA 2 y 3: Genérico sin contexto / Educacional/admin
        is_generic = False
        for pattern in GENERIC_PATTERNS:
            if re.search(pattern, desc_normalized):
                is_generic = True
                logger.debug(
                    f"Recomendación filtrada (genérico sin contexto): '{descripcion}'"
                )
                break

        if is_generic:
            continue

        # Si pasa todas las reglas → conservar
        filtered.append(rec)

    logger.info(
        f"Filtrado de recomendaciones: {len(recomendaciones)} → {len(filtered)} "
        f"({len(recomendaciones) - len(filtered)} genéricas eliminadas)"
    )

    return filtered


__all__ = ['filter_recommendations']
