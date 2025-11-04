"""
Tests para validadores de historias clínicas.
"""

from datetime import date

import pytest

from src.config.schemas import Diagnostico
from src.processors.validators import CIE10Validator, DateValidator


class TestCIE10Validator:
    """Tests para validación de códigos CIE-10."""

    def test_valid_cie10_codes(self):
        """Códigos CIE-10 válidos deben pasar la validación."""
        valid_codes = [
            "M54.5",  # Lumbalgia
            "J30.1",  # Rinitis alérgica
            "H52.0",  # Hipermetropía
            "E11.9",  # Diabetes tipo 2
            "I10.0",  # Hipertensión esencial
        ]

        for code in valid_codes:
            is_valid, error = CIE10Validator.validate_format(code)
            assert is_valid, f"Código {code} debería ser válido. Error: {error}"

    def test_invalid_cie10_codes(self):
        """Códigos CIE-10 inválidos deben fallar la validación."""
        invalid_codes = [
            "M545",     # Falta el punto
            "M54.50",   # Demasiados dígitos después del punto
            "M54",      # Falta el decimal
            "54.5",     # Falta la letra
            "MM54.5",   # Dos letras
            "",         # Vacío
        ]

        for code in invalid_codes:
            is_valid, error = CIE10Validator.validate_format(code)
            assert not is_valid, f"Código {code} debería ser inválido"
            assert error is not None

    def test_validate_diagnosis_list_empty(self):
        """Lista vacía de diagnósticos debe generar alerta."""
        alertas = CIE10Validator.validate_diagnosis_list([])

        assert len(alertas) == 1
        assert alertas[0].tipo == "dato_faltante"
        assert alertas[0].severidad == "alta"

    def test_validate_diagnosis_list_with_invalid_code(self):
        """Diagnóstico con código inválido debe generar alerta."""
        diagnosticos = [
            Diagnostico(
                codigo_cie10="M545",  # Formato inválido
                descripcion="Lumbalgia",
                tipo="principal",
                confianza=1.0
            )
        ]

        alertas = CIE10Validator.validate_diagnosis_list(diagnosticos)

        # Debe haber al menos una alerta por el código inválido
        assert len(alertas) > 0
        assert any(a.tipo == "formato_incorrecto" for a in alertas)


class TestDateValidator:
    """Tests para validación de fechas."""

    def test_valid_emo_date(self):
        """Fecha de EMO válida no debe generar alertas."""
        fecha = date.today()
        alertas = DateValidator.validate_emo_date(fecha)

        assert len(alertas) == 0

    def test_missing_emo_date(self):
        """Fecha de EMO faltante debe generar alerta."""
        alertas = DateValidator.validate_emo_date(None)

        assert len(alertas) == 1
        assert alertas[0].tipo == "dato_faltante"
        assert alertas[0].severidad == "alta"

    def test_future_date(self):
        """Fecha futura debe ser inválida."""
        future_date = date(2099, 12, 31)
        is_valid, error = DateValidator.validate_date_range(future_date)

        assert not is_valid
        assert "futura" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
