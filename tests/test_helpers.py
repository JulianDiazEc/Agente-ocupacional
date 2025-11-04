"""
Tests para funciones auxiliares.
"""

from datetime import date

import pytest

from src.utils.helpers import (
    calculate_age,
    calculate_imc,
    classify_imc,
    extract_cie10_codes,
    normalize_filename,
    parse_date_flexible,
    truncate_text,
)


class TestFileHelpers:
    """Tests para funciones de archivos."""

    def test_normalize_filename(self):
        """Normalización de nombres de archivo."""
        assert normalize_filename("Historia Clínica #123.pdf") == "historia_clinica_123.pdf"
        assert normalize_filename("HC 001 - Juan Pérez.pdf") == "hc_001_juan_perez.pdf"
        assert normalize_filename("  Archivo   Con   Espacios  .txt") == "archivo_con_espacios.txt"


class TestDateHelpers:
    """Tests para funciones de fechas."""

    def test_parse_date_flexible_iso_format(self):
        """Parseo de fecha en formato ISO."""
        result = parse_date_flexible("2024-03-15")
        assert result == date(2024, 3, 15)

    def test_parse_date_flexible_slash_format(self):
        """Parseo de fecha con barras (dd/mm/yyyy)."""
        result = parse_date_flexible("15/03/2024")
        assert result == date(2024, 3, 15)

    def test_parse_date_flexible_invalid(self):
        """Fecha inválida debe retornar None."""
        assert parse_date_flexible("invalid date") is None
        assert parse_date_flexible("") is None
        assert parse_date_flexible(None) is None

    def test_calculate_age(self):
        """Cálculo de edad."""
        birth_date = date(1990, 5, 15)
        reference_date = date(2024, 3, 15)

        age = calculate_age(birth_date, reference_date)
        assert age == 33  # No ha cumplido años aún en marzo

        # Después del cumpleaños
        reference_date = date(2024, 6, 15)
        age = calculate_age(birth_date, reference_date)
        assert age == 34


class TestMedicalHelpers:
    """Tests para funciones médicas."""

    def test_calculate_imc(self):
        """Cálculo de IMC."""
        # IMC = peso / (talla_m ** 2)
        # 70kg / (1.70m ** 2) = 24.22
        imc = calculate_imc(70.0, 170.0)
        assert imc == pytest.approx(24.22, abs=0.01)

    def test_calculate_imc_invalid(self):
        """IMC con valores inválidos debe lanzar error."""
        with pytest.raises(ValueError):
            calculate_imc(0, 170)

        with pytest.raises(ValueError):
            calculate_imc(70, 0)

    def test_classify_imc(self):
        """Clasificación de IMC."""
        assert classify_imc(24.5) == "Normal"
        assert classify_imc(18.0) == "Delgadez leve"
        assert classify_imc(27.0) == "Sobrepeso"
        assert classify_imc(32.0) == "Obesidad grado I"
        assert classify_imc(41.0) == "Obesidad grado III (mórbida)"


class TestTextHelpers:
    """Tests para funciones de texto."""

    def test_extract_cie10_codes(self):
        """Extracción de códigos CIE-10 de texto."""
        text = "Diagnósticos: M54.5 (Lumbalgia), J30.1 (Rinitis alérgica), E11.9 (Diabetes)"
        codes = extract_cie10_codes(text)

        assert len(codes) == 3
        assert "M54.5" in codes
        assert "J30.1" in codes
        assert "E11.9" in codes

    def test_extract_cie10_codes_no_matches(self):
        """Texto sin códigos CIE-10 debe retornar lista vacía."""
        text = "Este texto no tiene códigos CIE-10"
        codes = extract_cie10_codes(text)

        assert len(codes) == 0

    def test_truncate_text(self):
        """Truncado de texto."""
        text = "Este es un texto muy largo que necesita ser truncado"
        truncated = truncate_text(text, max_length=20)

        assert len(truncated) <= 20
        assert truncated.endswith("...")

    def test_truncate_text_short(self):
        """Texto corto no debe ser truncado."""
        text = "Texto corto"
        truncated = truncate_text(text, max_length=100)

        assert truncated == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
