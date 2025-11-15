"""
Validadores para el backend
"""
from werkzeug.datastructures import FileStorage


ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename: str) -> bool:
    """
    Validar que el archivo tiene una extensión permitida

    Args:
        filename: Nombre del archivo

    Returns:
        True si la extensión es permitida
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_size(file: FileStorage) -> bool:
    """
    Validar que el archivo no excede el tamaño máximo

    Args:
        file: Archivo a validar

    Returns:
        True si el tamaño es válido
    """
    # Mover el cursor al final para obtener el tamaño
    file.seek(0, 2)
    size = file.tell()

    # Regresar el cursor al inicio
    file.seek(0)

    return size <= MAX_FILE_SIZE
