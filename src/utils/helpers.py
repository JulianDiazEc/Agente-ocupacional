"""
Funciones auxiliares para procesamiento de historias clínicas.
"""

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from dateutil import parser as date_parser


def normalize_filename(filename: str) -> str:
    """
    Normaliza un nombre de archivo para uso consistente.

    Args:
        filename: Nombre original del archivo

    Returns:
        str: Nombre normalizado (sin espacios, caracteres especiales)

    Example:
        >>> normalize_filename("Historia Clínica #123.pdf")
        'historia_clinica_123.pdf'
    """
    # Convertir a minúsculas
    filename = filename.lower()

    # Reemplazar espacios y caracteres especiales con guión bajo
    filename = re.sub(r'[^a-z0-9._-]', '_', filename)

    # Eliminar guiones bajos duplicados
    filename = re.sub(r'_{2,}', '_', filename)

    return filename


def parse_date_flexible(date_string: str) -> Optional[date]:
    """
    Parsea una fecha en múltiples formatos posibles.

    Soporta formatos comunes en historias clínicas colombianas:
    - dd/mm/yyyy
    - yyyy-mm-dd (ISO)
    - dd-mm-yyyy
    - "15 de marzo de 2024"
    - "marzo 2024" (asume día 1)

    Args:
        date_string: String con la fecha a parsear

    Returns:
        date: Objeto date parseado, o None si no se pudo parsear

    Example:
        >>> parse_date_flexible("15/03/2024")
        datetime.date(2024, 3, 15)
        >>> parse_date_flexible("marzo 2024")
        datetime.date(2024, 3, 1)
    """
    if not date_string or not isinstance(date_string, str):
        return None

    # Limpiar string
    date_string = date_string.strip()

    try:
        # Intentar parseo automático con dateutil
        parsed = date_parser.parse(date_string, dayfirst=True, fuzzy=True)
        return parsed.date()
    except (ValueError, TypeError):
        pass

    # Patrones específicos de formato colombiano
    patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # dd/mm/yyyy o dd-mm-yyyy
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # yyyy-mm-dd o yyyy/mm/dd
    ]

    for pattern in patterns:
        match = re.search(pattern, date_string)
        if match:
            try:
                groups = match.groups()
                if len(groups[0]) == 4:  # yyyy-mm-dd
                    year, month, day = map(int, groups)
                else:  # dd-mm-yyyy
                    day, month, year = map(int, groups)
                return date(year, month, day)
            except (ValueError, TypeError):
                continue

    return None


def calculate_age(birth_date: date, reference_date: Optional[date] = None) -> int:
    """
    Calcula la edad en años dada una fecha de nacimiento.

    Args:
        birth_date: Fecha de nacimiento
        reference_date: Fecha de referencia (por defecto, hoy)

    Returns:
        int: Edad en años

    Example:
        >>> birth = date(1990, 5, 15)
        >>> calculate_age(birth, reference_date=date(2024, 3, 15))
        33
    """
    if reference_date is None:
        reference_date = date.today()

    age = reference_date.year - birth_date.year

    # Ajustar si aún no ha cumplido años este año
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age


def calculate_imc(peso_kg: float, talla_cm: float) -> float:
    """
    Calcula el Índice de Masa Corporal (IMC).

    Args:
        peso_kg: Peso en kilogramos
        talla_cm: Talla en centímetros

    Returns:
        float: IMC calculado (redondeado a 2 decimales)

    Example:
        >>> calculate_imc(70.0, 170.0)
        24.22
    """
    if talla_cm <= 0 or peso_kg <= 0:
        raise ValueError("Peso y talla deben ser valores positivos")

    talla_m = talla_cm / 100.0
    imc = peso_kg / (talla_m ** 2)
    return round(imc, 2)


def classify_imc(imc: float) -> str:
    """
    Clasifica el IMC según estándares OMS.

    Args:
        imc: Índice de Masa Corporal

    Returns:
        str: Clasificación del IMC

    Example:
        >>> classify_imc(24.5)
        'Normal'
    """
    if imc < 16:
        return "Delgadez severa"
    elif imc < 17:
        return "Delgadez moderada"
    elif imc < 18.5:
        return "Delgadez leve"
    elif imc < 25:
        return "Normal"
    elif imc < 30:
        return "Sobrepeso"
    elif imc < 35:
        return "Obesidad grado I"
    elif imc < 40:
        return "Obesidad grado II"
    else:
        return "Obesidad grado III (mórbida)"


def generate_file_hash(file_path: Path) -> str:
    """
    Genera un hash SHA256 de un archivo.

    Útil para detectar duplicados y verificar integridad.

    Args:
        file_path: Ruta al archivo

    Returns:
        str: Hash SHA256 en hexadecimal

    Example:
        >>> generate_file_hash(Path("documento.pdf"))
        'a1b2c3d4e5f6...'
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Leer en chunks para archivos grandes
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def safe_json_loads(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Carga JSON de forma segura, manejando errores comunes.

    Intenta corregir JSON malformado antes de fallar.

    Args:
        json_string: String con contenido JSON

    Returns:
        dict: Diccionario parseado, o None si falla

    Example:
        >>> safe_json_loads('{"key": "value"}')
        {'key': 'value'}
    """
    if not json_string:
        return None

    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        pass

    # Intentar limpiar el JSON
    try:
        # Eliminar markdown code blocks si existen
        cleaned = re.sub(r'^```json\s*|\s*```$', '', json_string.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'^```\s*|\s*```$', '', cleaned.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    return None


def extract_cie10_codes(text: str) -> list[str]:
    """
    Extrae códigos CIE-10 de un texto.

    Busca patrones como: M54.5, J30.1, E11.9, etc.

    Args:
        text: Texto donde buscar códigos CIE-10

    Returns:
        list[str]: Lista de códigos CIE-10 encontrados

    Example:
        >>> extract_cie10_codes("Diagnósticos: M54.5 (Lumbalgia), J30.1 (Rinitis)")
        ['M54.5', 'J30.1']
    """
    # Patrón: Letra mayúscula + 2 dígitos + punto + 1 dígito
    pattern = r'\b[A-Z]\d{2}\.\d\b'
    matches = re.findall(pattern, text)
    return list(set(matches))  # Eliminar duplicados


def format_file_size(size_bytes: int) -> str:
    """
    Formatea un tamaño de archivo en formato legible.

    Args:
        size_bytes: Tamaño en bytes

    Returns:
        str: Tamaño formateado (KB, MB, GB)

    Example:
        >>> format_file_size(1536)
        '1.50 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca un texto a una longitud máxima.

    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar si se trunca

    Returns:
        str: Texto truncado

    Example:
        >>> truncate_text("Este es un texto muy largo", max_length=10)
        'Este es...'
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)].rstrip() + suffix


class DateTimeEncoder(json.JSONEncoder):
    """
    JSONEncoder personalizado para serializar objetos datetime y date.

    Example:
        >>> import json
        >>> data = {"fecha": date(2024, 3, 15)}
        >>> json.dumps(data, cls=DateTimeEncoder)
        '{"fecha": "2024-03-15"}'
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


__all__ = [
    "normalize_filename",
    "parse_date_flexible",
    "calculate_age",
    "calculate_imc",
    "classify_imc",
    "generate_file_hash",
    "safe_json_loads",
    "extract_cie10_codes",
    "format_file_size",
    "truncate_text",
    "DateTimeEncoder",
]
