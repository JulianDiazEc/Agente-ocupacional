"""
Validadores de campos críticos en historias clínicas.

Incluye validación de CIE-10, fechas, rangos de valores, etc.
"""

import re
import unicodedata
from datetime import date
from typing import List, Optional, Tuple

from src.config.schemas import (
    Alerta,
    Diagnostico,
    Examen,
    HistoriaClinicaEstructurada,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


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


class CIE10Validator:
    """
    Validador de códigos CIE-10.

    Valida formato y opcionalmente contra catálogo oficial.
    """

    # Patrón para código CIE-10 (flexible):
    # - Corto: N80, M50 (letra + 2 dígitos)
    # - Completo: H52.1, M54.5 (letra + 2 dígitos + punto + 1-2 dígitos)
    CIE10_PATTERN = re.compile(r'^[A-Z]\d{2}(\.\d{1,2})?$')

    # Rangos válidos de capítulos CIE-10
    VALID_CHAPTERS = {
        'A': (0, 99),   # Enfermedades infecciosas
        'B': (0, 99),   # Enfermedades infecciosas
        'C': (0, 97),   # Neoplasias malignas
        'D': (0, 89),   # Enfermedades de la sangre
        'E': (0, 90),   # Enfermedades endocrinas
        'F': (0, 99),   # Trastornos mentales
        'G': (0, 99),   # Enfermedades del sistema nervioso
        'H': (0, 95),   # Enfermedades de ojos y oídos
        'I': (0, 99),   # Enfermedades del sistema circulatorio
        'J': (0, 99),   # Enfermedades del sistema respiratorio
        'K': (0, 93),   # Enfermedades del sistema digestivo
        'L': (0, 99),   # Enfermedades de la piel
        'M': (0, 99),   # Enfermedades del sistema osteomuscular
        'N': (0, 99),   # Enfermedades del sistema genitourinario
        'O': (0, 99),   # Embarazo, parto
        'P': (0, 96),   # Condiciones perinatales
        'Q': (0, 99),   # Malformaciones congénitas
        'R': (0, 99),   # Síntomas y signos
        'S': (0, 99),   # Traumatismos
        'T': (0, 98),   # Traumatismos múltiples
        'V': (0, 99),   # Causas externas
        'W': (0, 99),   # Causas externas
        'X': (0, 99),   # Causas externas
        'Y': (0, 98),   # Causas externas
        'Z': (0, 99),   # Factores que influyen en el estado de salud
    }

    @classmethod
    def validate_format(cls, code: str) -> Tuple[bool, Optional[str]]:
        """
        Valida el formato de un código CIE-10.

        ACEPTA formatos cortos (N80, M50) y completos (H52.1, M54.5).
        NUNCA rechaza por formato - problemas van a alertas, no ValidationError.

        Args:
            code: Código CIE-10 a validar

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_warning)
            - (True, None): Formato completo correcto
            - (True, "warning"): Formato corto pero aceptable
            - (False, "error"): Solo rechaza si es completamente inválido

        Example:
            >>> CIE10Validator.validate_format("M54.5")
            (True, None)
            >>> CIE10Validator.validate_format("M50")
            (True, "Formato corto sin subcategoría (recomendado: M50.X)")
            >>> CIE10Validator.validate_format("XYZ")
            (False, "Formato completamente inválido")
        """
        if not code:
            return False, "Código vacío"

        # Convertir a mayúsculas
        code = code.upper().strip()

        # Validar patrón básico
        if not cls.CIE10_PATTERN.match(code):
            return False, f"Formato inválido: debe ser N80 o M54.5. Recibido: {code}"

        # Validar capítulo
        chapter = code[0]
        if chapter not in cls.VALID_CHAPTERS:
            return False, f"Capítulo inválido: {chapter}"

        # Validar rango numérico del capítulo
        try:
            number = int(code[1:3])
            min_num, max_num = cls.VALID_CHAPTERS[chapter]
            if not (min_num <= number <= max_num):
                return False, f"Número fuera de rango para capítulo {chapter}: {number}"
        except ValueError:
            return False, f"Número inválido en código: {code[1:3]}"

        # Si llega aquí: código es válido
        # Advertencia si es formato corto (sin subcategoría)
        if '.' not in code:
            return True, f"Formato corto sin subcategoría (recomendado agregar: {code}.X)"

        return True, None

    @classmethod
    def validate_diagnosis_list(cls, diagnosticos: List[Diagnostico]) -> List[Alerta]:
        """
        Valida una lista de diagnósticos.

        Args:
            diagnosticos: Lista de diagnósticos a validar

        Returns:
            List[Alerta]: Alertas generadas
        """
        alertas = []

        if not diagnosticos:
            alertas.append(
                Alerta(
                    tipo="dato_faltante",
                    severidad="alta",
                    campo_afectado="diagnosticos",
                    descripcion="No se encontraron diagnósticos en la historia clínica",
                    accion_sugerida="Verificar que la HC contenga diagnósticos o que la extracción fue completa"
                )
            )
            return alertas

        # Validar cada diagnóstico
        for i, diag in enumerate(diagnosticos):
            is_valid, error_msg = cls.validate_format(diag.codigo_cie10)

            if not is_valid:
                # Formato completamente inválido → alerta ALTA
                alertas.append(
                    Alerta(
                        tipo="formato_incorrecto",
                        severidad="alta",
                        campo_afectado=f"diagnosticos[{i}].codigo_cie10",
                        descripcion=f"Código CIE-10 inválido: {diag.codigo_cie10}. {error_msg}",
                        accion_sugerida="Corregir el código CIE-10 manualmente"
                    )
                )
            elif error_msg:
                # Formato corto pero aceptable → alerta BAJA (warning)
                alertas.append(
                    Alerta(
                        tipo="formato_incorrecto",
                        severidad="baja",
                        campo_afectado=f"diagnosticos[{i}].codigo_cie10",
                        descripcion=f"Código CIE-10 en formato corto: {diag.codigo_cie10}. {error_msg}",
                        accion_sugerida="Agregar subcategoría si está disponible en el documento"
                    )
                )

            # Validar confianza baja
            if diag.confianza < 0.7:
                alertas.append(
                    Alerta(
                        tipo="dato_faltante",
                        severidad="media",
                        campo_afectado=f"diagnosticos[{i}]",
                        descripcion=f"Diagnóstico con confianza baja ({diag.confianza:.2f}): {diag.descripcion}",
                        accion_sugerida="Verificar manualmente el diagnóstico en el documento original"
                    )
                )

        # ELIMINADO: Validación de "diagnóstico principal"
        # No existe concepto obligatorio de diagnóstico principal/secundario en este contexto
        # (Regla 3 anti-false-positive: diagnosticos.tipo solo cuando explícito)

        return alertas


class DateValidator:
    """Validador de fechas."""

    @staticmethod
    def validate_date_range(
        fecha: date,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida que una fecha esté en un rango válido.

        Args:
            fecha: Fecha a validar
            min_date: Fecha mínima permitida (opcional)
            max_date: Fecha máxima permitida (default: hoy)

        Returns:
            Tuple[bool, str]: (es_valida, mensaje_error)
        """
        if max_date is None:
            max_date = date.today()

        if min_date and fecha < min_date:
            return False, f"Fecha muy antigua: {fecha} (mínima: {min_date})"

        if fecha > max_date:
            return False, f"Fecha futura: {fecha} (máxima: {max_date})"

        return True, None

    @staticmethod
    def validate_emo_date(fecha_emo: Optional[date]) -> List[Alerta]:
        """
        Valida la fecha de un EMO.

        Args:
            fecha_emo: Fecha del examen médico

        Returns:
            List[Alerta]: Alertas generadas
        """
        alertas = []

        if fecha_emo is None:
            alertas.append(
                Alerta(
                    tipo="dato_faltante",
                    severidad="alta",
                    campo_afectado="fecha_emo",
                    descripcion="No se encontró la fecha del examen médico ocupacional",
                    accion_sugerida="Localizar y agregar la fecha del EMO manualmente"
                )
            )
            return alertas

        # Validar rango razonable (últimos 5 años)
        min_date = date(date.today().year - 5, 1, 1)
        is_valid, error_msg = DateValidator.validate_date_range(fecha_emo, min_date=min_date)

        if not is_valid:
            alertas.append(
                Alerta(
                    tipo="formato_incorrecto",
                    severidad="media",
                    campo_afectado="fecha_emo",
                    descripcion=f"Fecha del EMO fuera de rango esperado: {error_msg}",
                    accion_sugerida="Verificar que la fecha sea correcta"
                )
            )

        return alertas


class ClinicalValueValidator:
    """Validador de valores clínicos (signos vitales, laboratorios, etc.)."""

    # Rangos normales para signos vitales
    VITAL_SIGNS_RANGES = {
        'presion_sistolica': (90, 140),
        'presion_diastolica': (60, 90),
        'frecuencia_cardiaca': (60, 100),
        'frecuencia_respiratoria': (12, 20),
        'temperatura': (36.0, 37.5),
        'saturacion_oxigeno': (95, 100),
        'imc': (18.5, 24.9),
    }

    @classmethod
    def validate_vital_signs(cls, signos_vitales) -> List[Alerta]:
        """
        Valida signos vitales y genera alertas para valores críticos.

        Args:
            signos_vitales: Objeto SignosVitales

        Returns:
            List[Alerta]: Alertas de valores críticos
        """
        alertas = []

        if not signos_vitales:
            return alertas

        # Validar presión arterial
        if signos_vitales.presion_arterial:
            match = re.match(r'(\d+)/(\d+)', signos_vitales.presion_arterial)
            if match:
                sistolica = int(match.group(1))
                diastolica = int(match.group(2))

                if sistolica >= 180 or diastolica >= 110:
                    alertas.append(
                        Alerta(
                            tipo="valor_critico",
                            severidad="alta",
                            campo_afectado="signos_vitales.presion_arterial",
                            descripcion=f"Presión arterial crítica: {signos_vitales.presion_arterial} mmHg (crisis hipertensiva)",
                            accion_sugerida="Requiere atención médica inmediata"
                        )
                    )
                elif sistolica >= 140 or diastolica >= 90:
                    alertas.append(
                        Alerta(
                            tipo="valor_critico",
                            severidad="media",
                            campo_afectado="signos_vitales.presion_arterial",
                            descripcion=f"Presión arterial elevada: {signos_vitales.presion_arterial} mmHg",
                            accion_sugerida="Considerar seguimiento y manejo de hipertensión"
                        )
                    )

        # Validar IMC
        if signos_vitales.imc:
            if signos_vitales.imc < 16:
                alertas.append(
                    Alerta(
                        tipo="valor_critico",
                        severidad="alta",
                        campo_afectado="signos_vitales.imc",
                        descripcion=f"IMC crítico bajo: {signos_vitales.imc} (delgadez severa)",
                        accion_sugerida="Evaluación nutricional urgente"
                    )
                )
            elif signos_vitales.imc >= 40:
                alertas.append(
                    Alerta(
                        tipo="valor_critico",
                        severidad="alta",
                        campo_afectado="signos_vitales.imc",
                        descripcion=f"IMC crítico alto: {signos_vitales.imc} (obesidad mórbida)",
                        accion_sugerida="Evaluación médica y nutricional especializada"
                    )
                )

        # Validar saturación de oxígeno
        if signos_vitales.saturacion_oxigeno and signos_vitales.saturacion_oxigeno < 90:
            alertas.append(
                Alerta(
                    tipo="valor_critico",
                    severidad="alta",
                    campo_afectado="signos_vitales.saturacion_oxigeno",
                    descripcion=f"Saturación de oxígeno crítica: {signos_vitales.saturacion_oxigeno}%",
                    accion_sugerida="Requiere evaluación respiratoria urgente"
                )
            )

        return alertas


def _check_visual_consistency(historia: HistoriaClinicaEstructurada) -> List[Alerta]:
    """
    Valida consistencia entre diagnósticos visuales y exámenes de optometría.

    Detecta:
    - Diagnóstico visual refractivo (H52.x: miopía, astigmatismo, hipermetropía)
    - Examen de optometría con visión corregida/normal

    Returns:
        List[Alerta]: Alertas de inconsistencia (severidad baja)
    """
    alertas = []

    # Códigos CIE-10 de problemas visuales refractivos
    VISUAL_DIAGNOSIS_CODES = {
        'H52.0': 'Hipermetropía',
        'H52.1': 'Miopía',
        'H52.2': 'Astigmatismo',
        'H52.3': 'Anisometropía',
        'H52.4': 'Presbicia'
    }

    # Buscar diagnósticos visuales
    diagnosticos_visuales = [
        diag for diag in historia.diagnosticos
        if any(diag.codigo_cie10.startswith(code[:4]) for code in VISUAL_DIAGNOSIS_CODES.keys())
    ]

    logger.debug(f"Validación visual: {len(diagnosticos_visuales)} diagnósticos visuales encontrados")
    if diagnosticos_visuales:
        for diag in diagnosticos_visuales:
            logger.debug(f"  - {diag.codigo_cie10}: {diag.descripcion}")

    if not diagnosticos_visuales:
        return alertas

    # Buscar exámenes de optometría
    examenes_visuales = [
        ex for ex in historia.examenes
        if ex.tipo == "optometria"
    ]

    logger.debug(f"Validación visual: {len(examenes_visuales)} exámenes de optometría encontrados")
    if examenes_visuales:
        for ex in examenes_visuales:
            logger.debug(f"  - Resultado: {ex.resultado}")
            logger.debug(f"  - Hallazgos: {ex.hallazgos_clave}")

    if not examenes_visuales:
        return alertas

    # Detectar inconsistencias
    for diag in diagnosticos_visuales:
        for exam in examenes_visuales:
            resultado = normalize_text(exam.resultado or "")
            hallazgos = normalize_text(exam.hallazgos_clave or "")

            # Indicadores de visión normal/corregida
            indicadores_normales = [
                "20/20", "20/25",
                "con correccion", "corregido", "corregida",
                "normal", "dentro de limites",
                "vision corregida", "ojo derecho 20/20", "ojo izquierdo 20/20"
            ]

            tiene_vision_normal = any(
                ind in resultado or ind in hallazgos
                for ind in indicadores_normales
            )

            if tiene_vision_normal:
                alertas.append(
                    Alerta(
                        tipo="inconsistencia_diagnostica",
                        severidad="baja",
                        campo_afectado="diagnosticos",
                        descripcion=(
                            f"Diagnóstico de {diag.descripcion} ({diag.codigo_cie10}) "
                            f"pero examen de optometría indica: {exam.resultado or exam.hallazgos_clave}"
                        ),
                        accion_sugerida=(
                            "Confirmar si el diagnóstico visual requiere corrección óptica actual "
                            "o es hallazgo leve/corregido. Revisar si aplica restricción laboral."
                        )
                    )
                )
                break  # No duplicar alerta por mismo diagnóstico

    return alertas


def _check_hearing_consistency(historia: HistoriaClinicaEstructurada) -> List[Alerta]:
    """
    Valida consistencia entre diagnósticos auditivos y exámenes de audiometría.

    Detecta:
    - Diagnóstico de hipoacusia/trauma acústico (H90.x, H91.x)
    - Audiometría con audición normal

    Returns:
        List[Alerta]: Alertas de inconsistencia (severidad baja)
    """
    alertas = []

    # Códigos CIE-10 de problemas auditivos
    HEARING_DIAGNOSIS_CODES = {
        'H90': 'Hipoacusia conductiva y neurosensorial',
        'H91': 'Otras pérdidas de audición',
        'H83.3': 'Efectos del ruido sobre el oído interno'
    }

    # Buscar diagnósticos auditivos
    diagnosticos_auditivos = [
        diag for diag in historia.diagnosticos
        if any(diag.codigo_cie10.startswith(code) for code in HEARING_DIAGNOSIS_CODES.keys())
    ]

    if not diagnosticos_auditivos:
        return alertas

    # Buscar exámenes de audiometría
    examenes_auditivos = [
        ex for ex in historia.examenes
        if ex.tipo == "audiometria"
    ]

    if not examenes_auditivos:
        return alertas

    # Detectar inconsistencias
    for diag in diagnosticos_auditivos:
        for exam in examenes_auditivos:
            resultado = normalize_text(exam.resultado or "")
            hallazgos = normalize_text(exam.hallazgos_clave or "")

            # Indicadores de audición normal
            indicadores_normales = [
                "audicion normal", "auditivamente normal",
                "bilateral normal", "dentro de limites normales",
                "sin perdida auditiva", "sin hipoacusia",
                "umbrales normales", "audiometria normal"
            ]

            tiene_audicion_normal = any(
                ind in resultado or ind in hallazgos
                for ind in indicadores_normales
            )

            if tiene_audicion_normal:
                alertas.append(
                    Alerta(
                        tipo="inconsistencia_diagnostica",
                        severidad="baja",
                        campo_afectado="diagnosticos",
                        descripcion=(
                            f"Diagnóstico de {diag.descripcion} ({diag.codigo_cie10}) "
                            f"pero audiometría indica: {exam.resultado or exam.hallazgos_clave}"
                        ),
                        accion_sugerida=(
                            "Confirmar si la hipoacusia se ha resuelto, es leve sin repercusión actual, "
                            "o si el diagnóstico requiere actualización. Revisar exposición a ruido."
                        )
                    )
                )
                break

    return alertas


def _check_respiratory_consistency(historia: HistoriaClinicaEstructurada) -> List[Alerta]:
    """
    Valida consistencia entre diagnósticos respiratorios y espirometría.

    Detecta:
    - Diagnóstico de EPOC/asma/afección respiratoria (J44.x, J45.x, J68.x)
    - Espirometría con función pulmonar normal

    Returns:
        List[Alerta]: Alertas de inconsistencia (severidad baja)
    """
    alertas = []

    # Códigos CIE-10 de problemas respiratorios ocupacionales
    RESPIRATORY_DIAGNOSIS_CODES = {
        'J44': 'EPOC (Enfermedad Pulmonar Obstructiva Crónica)',
        'J45': 'Asma',
        'J68': 'Afecciones respiratorias por químicos, gases, humos y vapores',
        'J60': 'Neumoconiosis de los mineros del carbón',
        'J61': 'Neumoconiosis debida al asbesto',
        'J62': 'Neumoconiosis debida a polvo de sílice'
    }

    # Buscar diagnósticos respiratorios
    diagnosticos_respiratorios = [
        diag for diag in historia.diagnosticos
        if any(diag.codigo_cie10.startswith(code) for code in RESPIRATORY_DIAGNOSIS_CODES.keys())
    ]

    if not diagnosticos_respiratorios:
        return alertas

    # Buscar exámenes de espirometría
    examenes_respiratorios = [
        ex for ex in historia.examenes
        if ex.tipo == "espirometria"
    ]

    if not examenes_respiratorios:
        return alertas

    # Detectar inconsistencias
    for diag in diagnosticos_respiratorios:
        for exam in examenes_respiratorios:
            resultado = normalize_text(exam.resultado or "")
            hallazgos = normalize_text(exam.hallazgos_clave or "")

            # Indicadores de función pulmonar normal
            indicadores_normales = [
                "funcion pulmonar normal", "funcion respiratoria normal",
                "espirometria normal", "patron normal",
                "sin obstruccion", "sin restriccion",
                "fev1 normal", "fvc normal",
                "dentro de limites normales", "parametros normales"
            ]

            tiene_funcion_normal = any(
                ind in resultado or ind in hallazgos
                for ind in indicadores_normales
            )

            if tiene_funcion_normal:
                alertas.append(
                    Alerta(
                        tipo="inconsistencia_diagnostica",
                        severidad="baja",
                        campo_afectado="diagnosticos",
                        descripcion=(
                            f"Diagnóstico de {diag.descripcion} ({diag.codigo_cie10}) "
                            f"pero espirometría indica: {exam.resultado or exam.hallazgos_clave}"
                        ),
                        accion_sugerida=(
                            "Confirmar si la condición respiratoria está controlada, es leve, "
                            "o si el diagnóstico requiere actualización. Revisar exposición a irritantes."
                        )
                    )
                )
                break

    return alertas


def validate_diagnosis_exam_consistency(historia: HistoriaClinicaEstructurada) -> List[Alerta]:
    """
    Valida consistencia entre diagnósticos y exámenes paraclínicos objetivos.

    Esta función se llama SOLO desde consolidate_person.py sobre el consolidado final.

    Detecta inconsistencias en:
    1. Diagnósticos visuales (H52.x) vs optometría
    2. Diagnósticos auditivos (H90.x, H91.x) vs audiometría
    3. Diagnósticos respiratorios (J44.x, J45.x, J68.x) vs espirometría

    NO valida:
    - Metabólicos (pueden estar controlados con medicación)
    - Cardiovasculares (mismo motivo)
    - Osteomusculares (dolor sin hallazgo objetivo es válido)

    Args:
        historia: Historia clínica consolidada

    Returns:
        List[Alerta]: Alertas de inconsistencia (severidad baja)
    """
    alertas = []

    logger.info(
        f"Ejecutando validación cruzada diagnóstico↔examen. "
        f"Diagnósticos: {len(historia.diagnosticos)}, Exámenes: {len(historia.examenes)}"
    )

    # Validaciones modulares
    alertas.extend(_check_visual_consistency(historia))
    alertas.extend(_check_hearing_consistency(historia))
    alertas.extend(_check_respiratory_consistency(historia))

    if alertas:
        logger.info(
            f"Validación cruzada diagnóstico↔examen: {len(alertas)} inconsistencias detectadas"
        )
    else:
        logger.info(
            f"Validación cruzada diagnóstico↔examen: Sin inconsistencias detectadas"
        )

    return alertas


def validate_examenes_criticos_sin_reflejo(historia: HistoriaClinicaEstructurada) -> List[Alerta]:
    """
    Valida que exámenes críticos/alterados tengan reflejo en diagnósticos/recomendaciones/restricciones.

    Un hallazgo crítico debe tener eco en:
    - diagnosticos, O
    - recomendaciones, O
    - restricciones_especificas

    Si no tiene reflejo → inconsistencia_diagnostica severidad baja.

    Esta función se llama SOLO desde consolidate_person.py sobre el consolidado final.

    Args:
        historia: Historia clínica consolidada

    Returns:
        List[Alerta]: Alertas de inconsistencia
    """
    alertas = []

    # Buscar exámenes con interpretacion critico/alterado
    examenes_criticos = [
        ex for ex in historia.examenes
        if ex.interpretacion and ex.interpretacion.lower() in ['critico', 'alterado']
    ]

    for exam in examenes_criticos:
        tipo = exam.tipo or ''
        hallazgos = exam.hallazgos_clave or ''

        # Verificar si hay reflejo en diagnósticos
        tiene_diagnostico = any(
            tipo.lower() in (diag.descripcion or '').lower()
            for diag in historia.diagnosticos
        )

        # Verificar si hay reflejo en recomendaciones
        tiene_recomendacion = any(
            tipo.lower() in (rec.descripcion or '').lower()
            for rec in historia.recomendaciones
        )

        # Verificar si hay reflejo en restricciones
        restricciones = historia.restricciones_especificas or ''
        tiene_restriccion = tipo.lower() in restricciones.lower()

        # Si no tiene reflejo en ningún lado, alerta
        if not (tiene_diagnostico or tiene_recomendacion or tiene_restriccion):
            alertas.append(
                Alerta(
                    tipo="inconsistencia_diagnostica",
                    severidad="baja",
                    campo_afectado="examenes",
                    descripcion=(
                        f"Examen {exam.interpretacion} de {tipo} con hallazgo '{hallazgos[:80]}' "
                        f"sin reflejo en diagnósticos, recomendaciones o restricciones"
                    ),
                    accion_sugerida=(
                        "Verificar si el hallazgo requiere diagnóstico CIE-10, "
                        "recomendación médica o restricción laboral específica"
                    )
                )
            )

    return alertas


def validate_historia_completa(historia: HistoriaClinicaEstructurada) -> List[Alerta]:
    """
    Ejecuta todas las validaciones sobre una historia clínica.

    Validaciones condicionales según tipo_documento_fuente:
    - examen_especifico: Solo valida datos presentes (no genera alertas por falta de datos generales)
    - hc_completa / cmo: Valida todos los campos esperados

    Args:
        historia: Historia clínica a validar

    Returns:
        List[Alerta]: Todas las alertas generadas
    """
    alertas = []

    # Determinar si es examen específico
    es_examen_especifico = historia.tipo_documento_fuente == "examen_especifico"

    # Validar diagnósticos (siempre, pero solo alerta de faltantes si NO es examen específico)
    if historia.diagnosticos:
        # Si hay diagnósticos, validar formato
        alertas.extend(CIE10Validator.validate_diagnosis_list(historia.diagnosticos))
    elif not es_examen_especifico:
        # Solo alertar de falta de diagnósticos si NO es examen específico
        alertas.append(
            Alerta(
                tipo="dato_faltante",
                severidad="alta",
                campo_afectado="diagnosticos",
                descripcion="No se encontraron diagnósticos en la historia clínica",
                accion_sugerida="Verificar que la HC contenga diagnósticos o que la extracción fue completa"
            )
        )

    # Validar fecha EMO (solo si NO es examen específico)
    if not es_examen_especifico:
        alertas.extend(DateValidator.validate_emo_date(historia.fecha_emo))

    # Validar signos vitales (solo si están presentes O si NO es examen específico)
    if historia.signos_vitales:
        # Si hay signos vitales, validar valores críticos
        alertas.extend(ClinicalValueValidator.validate_vital_signs(historia.signos_vitales))
    elif not es_examen_especifico:
        # Opcional: alertar de falta de signos vitales solo en HC completa
        pass  # No alertamos por ahora, puede ser normal en CMO

    # Validar aptitud laboral (solo si NO es examen específico)
    if not es_examen_especifico:
        if historia.aptitud_laboral is None:
            alertas.append(
                Alerta(
                    tipo="dato_faltante",
                    severidad="alta",
                    campo_afectado="aptitud_laboral",
                    descripcion="No se encontró el concepto de aptitud laboral",
                    accion_sugerida="Solicitar al médico ocupacional que emita concepto de aptitud"
                )
            )

    # Validar restricciones sin justificación (siempre)
    if historia.restricciones_especificas and not historia.diagnosticos:
        alertas.append(
            Alerta(
                tipo="inconsistencia_diagnostica",
                severidad="media",
                campo_afectado="restricciones_especificas",
                descripcion="Se especifican restricciones pero no hay diagnósticos que las justifiquen",
                accion_sugerida="Verificar diagnósticos asociados a las restricciones"
            )
        )

    tipo_doc = historia.tipo_documento_fuente
    logger.info(f"Validación completa ({tipo_doc}): {len(alertas)} alertas generadas")

    return alertas


__all__ = [
    "CIE10Validator",
    "DateValidator",
    "ClinicalValueValidator",
    "validate_historia_completa",
    "validate_diagnosis_exam_consistency",
    "validate_examenes_criticos_sin_reflejo"
]
