# tools — Utilidades y scripts de soporte

Este directorio contiene scripts auxiliares para diagnóstico, validación y exportación. Están pensados para ejecutarse en Windows PowerShell, con el entorno del proyecto activado.

## Scripts incluidos

- `print_routes.py`: lista rutas/blueprints de la aplicación Flask, útil para verificar disponibilidad de endpoints y detectar conflictos.
- `test_v2_graph.py`: ejercicio de construcción/visualización de grafos; sirve como smoke test de dependencias (NetworkX, parsers PDB) y de configuración local.
- `test_v2_export.py`: prueba de exportes (XLSX) por toxina/familia/WT; valida nombres de hojas/archivos y columnas homogéneas.
- `test_v2_dipole.py`: verificación del cálculo de momento dipolar (aprox. y PDB+PSF) y coherencia de magnitud/dirección.
- `test_v2_peptides.py`: pruebas de extracción/segmentación a péptido maduro desde entradas de la BD.
- `test_temp_files.py`: asegura limpieza de temporales y permisos de escritura en exportaciones.

## Ejecución

Ejemplo en PowerShell (desde la raíz del proyecto):

```powershell
# Rutas absolutas recomendadas en Windows
python .\tools\test_v2_graph.py
python .\tools\test_v2_export.py
```

Consejos:

- Use entorno con dependencias instaladas (pandas, openpyxl, networkx, biopython, mdanalysis si aplica).
- Evite ejecutar scripts de exportación si tiene archivos XLSX abiertos (bloqueo de Windows).

## Salidas y limpieza

- Los scripts pueden generar carpetas temporales y XLSX en `./exports/` o `./deliverables/`.
- `test_temp_files.py` ayuda a detectar temporales huérfanos; borre manualmente si el proceso fue interrumpido.

## Seguridad y reproducibilidad

- No exponen secretos; no hacen llamadas externas salvo endpoints locales.
- Imprimen versiones y rutas críticas cuando aplica; guarde el log de consola para trazabilidad.
