# psfs — Archivos PSF (Protein Structure File) asociados a toxinas

Este directorio contiene archivos PSF para toxinas del conjunto Nav1.7 y variantes relacionadas, utilizados para cálculos que requieren
parámetros atómicos explícitos (cargas, tipos atómicos, conectividad), como la estimación precisa del
**momento dipolar** y análisis estructurales dependientes de conectividad a nivel de átomo.

## Alcance

- PSF curados y alineados uno a uno con sus PDB correspondientes en `../pdbs/` (mismo nombre base).
- Destinados a toxinas WT y mutantes empleadas en comparativas dentro del conjunto Nav1.7.
- Formato compatible con lectores estándar (MDAnalysis, VMD, parsers internos del proyecto).

## Convenciones de nombre

- Mismo prefijo/base que el PDB correspondiente (p. ej., `μ-TRTX-Hh2a.psf` ↔ `μ-TRTX-Hh2a.pdb`).
- Mutaciones expresadas en el nombre siguiendo notación estándar (p. ej., `μ-TRTX-Hh2a_E1A_E4A_Y33W.psf`).
- Conservación de letras griegas cuando el sistema de archivos lo permite; de lo contrario, transliteración coherente con `pdbs/`.

## Relación con la base de datos y el pipeline

- Los PSF pueden ser insertados como BLOB en `database/toxins.db` mediante los loaders de `loaders/new_instert_Nav1_7_pdb_psf.py`.
- El par PDB+PSF se utiliza en módulos de análisis (p. ej., `graphs/graph_analysis2D.py`) para el cálculo del vector de **momento dipolar** con cargas atómicas reales.
- La visualización 3D en la aplicación puede proyectar la dirección del dipolo derivada de PDB+PSF.

## Uso operativo

- Cálculo de dipolo preciso: requiere cargar PDB y PSF de la misma toxina; el sistema toma posiciones 3D del PDB y cargas del PSF.
- Análisis de conectividad atómica: los PSF definen topología interna utilizada por parsers y validaciones.
- Coherencia de nombres/pares: el pipeline espera coincidencia exacta entre el nombre base del PDB y el del PSF.
