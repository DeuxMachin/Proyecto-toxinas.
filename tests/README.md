# tests — Suite de pruebas (unitarias e integración)

Este directorio organiza las pruebas del proyecto en dos niveles:

- `unit/`: pruebas unitarias de casos de uso, adaptadores y contratos (sin I/O externo cuando es posible).
- `integration/`: pruebas de integración extremo a extremo (endpoints Flask, exportaciones, paridad entre vistas y casos de uso).

## Cómo ejecutar

Desde la raíz del proyecto, en Windows PowerShell:

```powershell
# Ejecutar toda la suite
pytest -q

# Ejecutar por carpeta
pytest .\tests\unit -q
pytest .\tests\integration -q

# Ejecutar un archivo específico
pytest .\tests\unit\test_v2_graph_contract.py -q
```

Requisitos previos:

- Base de datos `database/toxins.db` poblada (Nav1.7) y estructuras locales en `pdbs/` y `psfs/`.
- Dependencias instaladas (pytest, pandas, networkx, biopython, openpyxl, etc.).

## Estructura

- `unit/test_build_protein_graph.py`: contrato del grafo (nodos, aristas, atributos mínimos).
- `unit/test_v2_graph_contract.py`: métricas y tipos de arista esperados; validaciones de comunidad.
- `unit/test_export_*`: contratos y formato de exportes (nombres de hoja/archivo, columnas homogéneas, orden).
- `unit/test_v2_families_endpoints.py` y `integration/test_v2_*`: endpoints funcionales, smoke tests de Flask y paridad con casos de uso.

## Buenas prácticas

- Evitar dependencias externas en unit; simular datos mínimos.
- Mantener independientes los tests de exportación (no abrir XLSX mientras se corre la suite).
- Documentar precondiciones (p. ej., presencia de PSF) cuando sean requeridas por la prueba.
