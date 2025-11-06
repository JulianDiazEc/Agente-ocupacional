"""
Validadores de campos críticos en historias clínicas.

Incluye validación de CIE-10, fechas, rangos de valores, etc.
"""

import re
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


class CIE10Validator:
    """
    Validador de códigos CIE-10.

    Valida formato y opcionalmente contra catálogo oficial.
    """

    # Patrón para código CIE-10: Letra + 2 dígitos + punto + 1 dígito
    CIE10_PATTERN = re.compile(r'^[A-Z]\d{2}\.\d$')

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

        Args:
            code: Código CIE-10 a validar

        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)

        Example:
            >>> CIE10Validator.validate_format("M54.5")
            (True, None)
            >>> CIE10Validator.validate_format("M545")
            (False, "Formato inválido: debe ser Letra##.# (ej: M54.5)")
        """
        if not code:
            return False, "Código vacío"

        # Convertir a mayúsculas
        code = code.upper().strip()

        # Validar patrón
        if not cls.CIE10_PATTERN.match(code):
            return False, f"Formato inválido: debe ser Letra##.# (ej: M54.5). Recibido: {code}"

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
                alertas.append(
                    Alerta(
                        tipo="formato_incorrecto",
                        severidad="alta",
                        campo_afectado=f"diagnosticos[{i}].codigo_cie10",
                        descripcion=f"Código CIE-10 inválido: {diag.codigo_cie10}. {error_msg}",
                        accion_sugerida="Corregir el código CIE-10 manualmente"
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

        # Validar que haya al menos un diagnóstico principal
        principales = [d for d in diagnosticos if d.tipo == "principal"]
        if not principales:
            alertas.append(
                Alerta(
                    tipo="inconsistencia_diagnostica",
                    severidad="media",
                    campo_afectado="diagnosticos",
                    descripcion="No se identificó ningún diagnóstico principal",
                    accion_sugerida="Verificar cuál diagnóstico debe ser el principal"
                )
            )

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
    "validate_historia_completa"
]
