#!/usr/bin/env python3
"""
Migra type hints de Python 3.10+ a 3.7+ para compatibilidad.
Uso: python tools/migrate_type_hints.py
"""
import re
from pathlib import Path
from typing import Set

def migrate_file(filepath: Path) -> bool:
    """Migra un archivo .py de sintaxis 3.10+ a 3.7+"""
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    # Patrones de reemplazo
    replacements = [
        # Union con |
        (r'\bint \| None\b', r'Optional[int]'),
        (r'\bstr \| None\b', r'Optional[str]'),
        (r'\bfloat \| None\b', r'Optional[float]'),
        (r'\bbool \| None\b', r'Optional[bool]'),
        (r'\bList\[str\] \| None\b', r'Optional[List[str]]'),
        (r'\bDict\[.*?\] \| None\b', lambda m: f'Optional[{m.group(0).split(" | ")[0]}]'),
        
        # Generic types sin typing
        (r'\blist\[([^\]]+)\]', r'List[\1]'),
        (r'\bdict\[([^\]]+),\s*([^\]]+)\]', r'Dict[\1, \2]'),
        (r'\btuple\[([^\]]+)\]', r'Tuple[\1]'),
        (r'\bset\[([^\]]+)\]', r'Set[\1]'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Detectar imports necesarios
    needed = set()
    if 'Optional[' in content and 'Optional' not in get_existing_imports(original):
        needed.add('Optional')
    if 'List[' in content and 'List' not in get_existing_imports(original):
        needed.add('List')
    if 'Dict[' in content and 'Dict' not in get_existing_imports(original):
        needed.add('Dict')
    if 'Tuple[' in content and 'Tuple' not in get_existing_imports(original):
        needed.add('Tuple')
    if 'Set[' in content and 'Set' not in get_existing_imports(original):
        needed.add('Set')
    
    # Agregar imports si es necesario
    if needed and content != original:
        content = add_typing_imports(content, needed)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return True
    return False

def get_existing_imports(content: str) -> Set[str]:
    """Extrae imports de typing ya presentes."""
    imports = set()
    for match in re.finditer(r'from typing import ([^\n]+)', content):
        items = match.group(1).split(',')
        imports.update(item.strip() for item in items)
    return imports

def add_typing_imports(content: str, needed: Set[str]) -> str:
    """Agrega imports de typing necesarios."""
    lines = content.split('\n')
    
    # Buscar línea de import de typing existente
    for i, line in enumerate(lines):
        if line.startswith('from typing import'):
            # Agregar a import existente
            existing = line.replace('from typing import', '').strip()
            items = [item.strip() for item in existing.split(',')]
            items.extend(sorted(needed))
            items = sorted(set(items))
            lines[i] = f"from typing import {', '.join(items)}"
            return '\n'.join(lines)
    
    # Si no existe, agregar después del último import
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_pos = i + 1
    
    new_import = f"from typing import {', '.join(sorted(needed))}"
    lines.insert(insert_pos, new_import)
    return '\n'.join(lines)

def main():
    project_root = Path(__file__).parent.parent
    
    # Archivos a procesar (excluir venv, cache, etc.)
    py_files = []
    for pattern in ['*.py', '**/*.py']:
        for f in project_root.glob(pattern):
            if any(exclude in str(f) for exclude in ['.venv', 'venv', '__pycache__', '.pytest_cache']):
                continue
            py_files.append(f)
    
    migrated = []
    for py_file in py_files:
        try:
            if migrate_file(py_file):
                migrated.append(py_file)
                print(f"✓ Migrado: {py_file.relative_to(project_root)}")
        except Exception as e:
            print(f"✗ Error en {py_file.relative_to(project_root)}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Total archivos procesados: {len(py_files)}")
    print(f"Archivos migrados: {len(migrated)}")
    print(f"{'='*60}")
    
    if migrated:
        print("\nArchivos modificados:")
        for f in migrated:
            print(f"  - {f.relative_to(project_root)}")

if __name__ == '__main__':
    main()