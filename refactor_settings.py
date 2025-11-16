#!/usr/bin/env python3
"""
Script de refactorización de importaciones de settings.

Refactoriza:
  from src.config.settings import settings

A:
  from src.config.settings import get_settings

  settings = get_settings()

Solo en archivos que realmente usen la variable settings.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class SettingsRefactorer:
    """Refactoriza imports de settings en archivos Python."""

    # Patrón para encontrar el import incorrecto
    IMPORT_PATTERN = re.compile(
        r'^(\s*)from\s+src\.config\.settings\s+import\s+settings\s*$',
        re.MULTILINE
    )

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.changes: List[Tuple[Path, str, str]] = []

    def should_skip_file(self, file_path: Path) -> bool:
        """Verifica si el archivo debe ser ignorado."""
        # No modificar el archivo settings.py mismo
        if file_path.name == 'settings.py':
            return True

        # Ignorar directorios especiales
        skip_dirs = {'__pycache__', '.venv', 'venv', 'node_modules', '.git'}
        return any(part in file_path.parts for part in skip_dirs)

    def file_uses_settings_variable(self, content: str, import_line_num: int) -> bool:
        """
        Verifica si el archivo usa la variable 'settings' después del import.

        Args:
            content: Contenido completo del archivo
            import_line_num: Número de línea donde está el import

        Returns:
            True si usa la variable settings después del import
        """
        lines = content.split('\n')

        # Revisar líneas después del import
        for i, line in enumerate(lines[import_line_num + 1:], start=import_line_num + 1):
            # Ignorar líneas vacías y comentarios
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Buscar uso de 'settings.' o 'settings['
            if re.search(r'\bsettings\s*[\.\[]', line):
                return True

            # Si encontramos otra definición de settings, no necesitamos agregar get_settings()
            if re.match(r'^\s*settings\s*=', line):
                return False

        return False

    def refactor_file(self, file_path: Path) -> Tuple[bool, str, str]:
        """
        Refactoriza un archivo.

        Returns:
            (changed, old_content, new_content)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Buscar el import incorrecto
        match = self.IMPORT_PATTERN.search(content)
        if not match:
            return (False, content, content)

        # Obtener la indentación del import
        indent = match.group(1)
        import_line_num = content[:match.start()].count('\n')

        # Verificar si el archivo realmente usa settings
        uses_settings = self.file_uses_settings_variable(content, import_line_num)

        # Construir el nuevo import
        new_import = f"{indent}from src.config.settings import get_settings"

        # Si usa settings, agregar la línea de inicialización
        if uses_settings:
            new_import += f"\n\n{indent}settings = get_settings()"

        # Reemplazar el import
        new_content = self.IMPORT_PATTERN.sub(new_import, content)

        return (True, content, new_content)

    def scan_directory(self, directory: Path):
        """Escanea un directorio buscando archivos a refactorizar."""
        for py_file in directory.rglob('*.py'):
            if self.should_skip_file(py_file):
                continue

            changed, old_content, new_content = self.refactor_file(py_file)

            if changed:
                self.changes.append((py_file, old_content, new_content))

    def show_diff(self):
        """Muestra un diff de los cambios propuestos."""
        if not self.changes:
            print("✅ No se encontraron archivos que necesiten refactorización.")
            return

        print(f"\n📋 Se encontraron {len(self.changes)} archivo(s) para refactorizar:\n")

        for file_path, old_content, new_content in self.changes:
            relative_path = file_path.relative_to(self.project_root)
            print(f"{'='*70}")
            print(f"📄 {relative_path}")
            print(f"{'='*70}\n")

            # Mostrar diff línea por línea
            old_lines = old_content.split('\n')
            new_lines = new_content.split('\n')

            # Encontrar las líneas que cambiaron
            for i, (old_line, new_line) in enumerate(zip(old_lines, new_lines), 1):
                if old_line != new_line:
                    if old_line.strip():
                        print(f"  - {i:4d} | {old_line}")
                    if new_line.strip():
                        print(f"  + {i:4d} | {new_line}")

            # Mostrar líneas nuevas si hay más en new_content
            if len(new_lines) > len(old_lines):
                for i, line in enumerate(new_lines[len(old_lines):], len(old_lines) + 1):
                    if line.strip():
                        print(f"  + {i:4d} | {line}")

            print()

    def apply_changes(self):
        """Aplica los cambios a los archivos."""
        if not self.changes:
            return

        print(f"\n🔧 Aplicando cambios a {len(self.changes)} archivo(s)...\n")

        for file_path, _, new_content in self.changes:
            # Crear backup
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                with open(file_path, 'r', encoding='utf-8') as orig:
                    f.write(orig.read())

            # Aplicar cambios
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            relative_path = file_path.relative_to(self.project_root)
            print(f"  ✅ {relative_path}")
            print(f"     (backup: {backup_path.name})")

        print(f"\n🎉 Refactorización completada!")
        print(f"\n💡 Backups creados con extensión .bak")
        print(f"   Para eliminar backups: find . -name '*.bak' -delete")


def main():
    """Función principal."""
    print("=" * 70)
    print("🔧 Refactorizador de Importaciones de Settings")
    print("=" * 70)

    # Obtener directorio del proyecto
    project_root = Path(__file__).parent

    # Directorios a escanear
    directories = [
        project_root / 'backend',
        project_root / 'src',
    ]

    # Crear refactorer
    refactorer = SettingsRefactorer(project_root)

    # Escanear directorios
    print(f"\n🔍 Escaneando directorios...")
    for directory in directories:
        if directory.exists():
            print(f"   - {directory.relative_to(project_root)}/")
            refactorer.scan_directory(directory)
        else:
            print(f"   ⚠️  {directory.relative_to(project_root)}/ no existe")

    # Mostrar diff
    refactorer.show_diff()

    # Preguntar si aplicar cambios
    if refactorer.changes:
        print(f"\n{'='*70}")
        response = input("\n¿Aplicar estos cambios? (s/N): ").strip().lower()

        if response in ('s', 'si', 'sí', 'y', 'yes'):
            refactorer.apply_changes()
        else:
            print("\n❌ Cambios cancelados.")

    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
