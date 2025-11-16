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

# Palabras clave que indican recomendación genérica (substring match)
GENERIC_KEYWORDS = [
    'capacitacion',
    'educacion en',
    'habitos saludables',
    'estilo de vida saludable',
    'pausas activas',
    'adherir lineamientos',
    'control segun pve',
    'lineamientos del ministerio',
]

# Patrones genéricos sin contexto (regex)
GENERIC_PATTERNS = [
    # EPP genérico (CUALQUIER uso de EPP sin especificidad)
    r'\buso\s+(adecuado\s+)?de\s+epp\b',  # Uso de EPP / Uso adecuado de EPP
    r'\bepp\s+(auditivo|visual|respiratorio)(?!.*por|debido|exposicion)',  # EPP tipo sin contexto
    r'uso\s+(adecuado|correcto|permanente|obligatorio)\s+de\s+(epp|elementos)',
    r'uso\s+de\s+proteccion\s+personal',
    r'elementos\s+de\s+proteccion\s+personal',

    # Educación/capacitación genérica
    r'\beducacion\s+en\b',  # Educación en X (sin contexto específico)
    r'\bcapacitacion\s+en\b',  # Capacitación en X (sin contexto específico)
    r'\bcapacitacion\s+(grupal|individual|periodica)',

    # Hábitos genéricos (MÁS AMPLIO)
    r'\bhabitos\s+(saludables|y\s+estilos)',  # Hábitos saludables o "hábitos y estilos"
    r'continuar\s+(o\s+)?(adoptar\s+)?habitos',  # Continuar/adoptar hábitos
    r'estilo\s+de\s+vida\s+saludable',
    r'mantener\s+habitos\s+saludables',
    r'adoptar\s+habitos\s+saludables',
    r'promover\s+habitos',

    # Fórmulas administrativas
    r'adherir\s+(a\s+)?(lineamientos|guias?|protocolos?)',
    r'seguir\s+(lineamientos|guias?|protocolos?)',
    r'control\s+segun\s+(pve|programa)',
    r'lineamientos\s+(del\s+ministerio|nacionales|internacionales)',
    r'cumplir\s+con\s+lineamientos',

    # Medidas genéricas sin parámetro
    r'\breposo\s+auditivo\b(?!.*\d+\s*(min|hora|hr))',  # reposo sin duración
    r'\bejercicio\s+fisico\b(?!.*\d+\s*(min|veces|sesiones))',  # ejercicio sin frecuencia
    r'\bfotoproteccion\b(?!.*fps|factor|exposicion)',  # fotoprotección sin contexto
    r'\buso\s+de\s+filtro\s+solar\b(?!.*fps|exposicion)',  # filtro solar sin contexto
    r'\buso\s+de\s+bloqueador\b(?!.*fps)',

    # Ejercicio/actividad genérica
    r'150\s+minutos.*ejercicio',  # Frase OMS genérica
    r'actividad\s+fisica\s+regular(?!.*\d+)',  # actividad sin parámetro
    r'realizar\s+ejercicio(?!.*\d+)',

    # Pausas genéricas
    r'pausas\s+activas(?!.*cada|\d+)',
    r'pausas\s+laborales(?!.*cada|\d+)',
    r'realizar\s+pausas(?!.*cada|\d+)',

    # Postura/ergonomía genérica
    r'buena\s+postura(?!.*por|debido)',
    r'higiene\s+postural(?!.*por|debido)',
    r'ergonomia\s+(del\s+)?(puesto\s+de\s+trabajo|laboral)(?!.*por|debido)',
    r'correccion\s+postural(?!.*por|debido)',

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

    Reglas de FILTRADO (eliminar si cumple CUALQUIERA):
    1. Longitud ≤ 3 palabras Y es nombre de examen conocido
    2. Contiene palabra clave genérica (capacitación, educación en, hábitos saludables, etc.)
    3. Coincide con patrón genérico (uso de EPP, pausas activas, ergonomía, etc.)

    Reglas de CONSERVACIÓN (conservar si cumple AL MENOS UNO):
    1. Tiene contexto clínico específico (números, diagnósticos, hallazgos, exposiciones)
    2. Tiene longitud > 3 palabras Y NO es genérico

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
            logger.debug("Recomendación conservada (contexto clínico): '%s...'", descripcion[:60])
            continue

        # REGLA 1: Nombre suelto de examen (≤3 palabras + es examen conocido)
        is_exam_name = False
        if palabra_count <= 3:
            for exam_term in EXAM_NAME_TERMS:
                if exam_term in desc_normalized:
                    is_exam_name = True
                    logger.debug(
                        f"Recomendación filtrada (nombre suelto de examen ≤3 palabras): '{descripcion}'"
                    )
                    break

        if is_exam_name:
            continue

        # REGLA 2: Contiene palabra clave genérica
        is_generic_keyword = False
        for keyword in GENERIC_KEYWORDS:
            if keyword in desc_normalized:
                is_generic_keyword = True
                logger.debug(
                    f"Recomendación filtrada (palabra clave genérica '{keyword}'): '{descripcion}'"
                )
                break

        if is_generic_keyword:
            continue

        # REGLA 3: Coincide con patrón genérico
        is_generic_pattern = False
        for pattern in GENERIC_PATTERNS:
            if re.search(pattern, desc_normalized):
                is_generic_pattern = True
                logger.debug(
                    f"Recomendación filtrada (patrón genérico): '{descripcion}'"
                )
                break

        if is_generic_pattern:
            continue

        # Si pasa todas las reglas → conservar
        filtered.append(rec)

    logger.info(
        f"Filtrado de recomendaciones: {len(recomendaciones)} → {len(filtered)} "
        f"({len(recomendaciones) - len(filtered)} genéricas eliminadas)"
    )

    return filtered


__all__ = ['filter_recommendations']
