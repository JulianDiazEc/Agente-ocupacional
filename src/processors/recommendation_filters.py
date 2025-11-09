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
    # EPP genérico (CUALQUIER uso de EPP sin especificidad)
    r'\buso\s+de\s+epp\b',  # Uso de EPP (cualquier variante)
    r'\bepp\s+(auditivo|visual|respiratorio)',  # EPP + tipo sin contexto
    r'uso\s+(adecuado|correcto|permanente|obligatorio)\s+de\s+(epp|elementos)',
    r'uso\s+de\s+proteccion\s+personal',
    r'elementos\s+de\s+proteccion\s+personal',

    # Educación/capacitación genérica
    r'educacion\s+en\s+(higiene|postura|autocuidado|estilos)',
    r'capacitacion\s+en\s+(autocuidado|estilos|habitos)',

    # Hábitos genéricos (MÁS AMPLIO)
    r'\bhabitos\s+(saludables|y\s+estilos)',  # Hábitos saludables o "hábitos y estilos"
    r'continuar\s+(o\s+)?(adoptar\s+)?habitos',  # Continuar/adoptar hábitos
    r'estilo\s+de\s+vida\s+saludable',
    r'mantener\s+habitos',
    r'adoptar\s+habitos',

    # Fórmulas administrativas
    r'adherir\s+(lineamientos|guia|protocolo|a\s+los\s+lineamientos)',
    r'seguir\s+(lineamientos|guia|protocolo)',
    r'control\s+segun\s+(pve|programa)',
    r'lineamientos\s+del\s+ministerio',
    r'lineamientos\s+(nacionales|internacionales|ministerio)',

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

    # Postura/ergonomía genérica
    r'buena\s+postura(?!.*por|debido)',
    r'higiene\s+postural(?!.*por|debido)',
    r'ergonomia\s+(puesto\s+de\s+trabajo|laboral)(?!.*por|debido)',  # Ergonomía genérica

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
    Verifica si la recomendación tiene contexto clínico ESPECÍFICO.

    Contexto clínico VÁLIDO (debe estar anclado a condición concreta):
    - Números con unidades médicas: 85 dB, 15 kg, IMC >30
    - Frecuencias temporales con números: cada 6 meses, 3 veces por semana
    - Causales médicos: por diagnóstico de X, por hallazgo de Y, por exposición a Z dB
    - Códigos CIE-10
    - Condiciones con parámetros medibles

    NO es contexto válido:
    - "puesto de trabajo", "cargo", "área" (genérico)
    - Frecuencias sin causales: "anual", "mensual" (sin decir por qué)

    Args:
        descripcion: Texto de la recomendación

    Returns:
        bool: True si tiene contexto clínico específico y anclado
    """
    desc_lower = descripcion.lower()

    # Indicadores de contexto clínico ESPECÍFICO
    clinical_indicators = [
        # Números con unidades médicas
        r'\d+\s*(mg|db|kg|mmhg|cm|mm|ml|litros|°c|grados|fps|hz|khz)',

        # Parámetros medibles
        r'(>|<|=|mayor\s+a|menor\s+a|superior\s+a|inferior\s+a)\s*\d+',
        r'\bimc\s*(>|<|=|mayor|menor)',
        r'nivel\s+de\s+\d+',

        # Códigos médicos (CIE-10)
        r'\b[A-Z]\d{2}\.\d\b',

        # Causales médicos ESPECÍFICOS (con condición concreta)
        r'por\s+(diagnostico\s+de|hallazgo\s+de|antecedente\s+de)\s+\w+',
        r'por\s+exposicion\s+a\s+\d+',  # Por exposición a X dB
        r'por\s+riesgo\s+de\s+\w+',
        r'debido\s+a\s+(diagnostico|hallazgo|exposicion)',
        r'relacionado\s+con\s+(diagnostico|hallazgo|patologia)',

        # Frecuencias CON causales (no solas)
        r'cada\s+\d+\s*(meses|semanas|dias|horas)\s+(por|debido|para)',
        r'\d+\s*(veces|sesiones)\s+por\s+(semana|mes)\s+(por|debido|para)',

        # Condiciones específicas con valores
        r'si\s+\w+\s+(>|<|=)\s*\d+',
        r'en\s+caso\s+de\s+\w+\s+(>|<|=)\s*\d+',
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
