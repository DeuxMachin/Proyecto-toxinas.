# pdbs — Estructuras PDB curadas para Nav1.7 y variantes

Este directorio contiene estructuras PDB locales utilizadas por el proyecto para análisis estructural, cálculo de métricas de grafo, y estimación del momento dipolar (en conjunto con PSF cuando está disponible).

## Alcance

- Conjunto curado de toxinas relacionadas a NaV1.7 (WT y mutantes) y algunas variantes de familias (μ/β/ω‑TRTX) usadas en comparativas.
- Archivos PDB recortados al péptido maduro cuando corresponde (según reglas de corte de OBJ1) y validados por continuidad y conectividad S–S.
- Subcarpeta `WT/` para referencias silvestres empleadas en comparación WT vs mutantes.

## Convenciones de nombre

- Formato base: `<familia>-<toxina>[_Mut1[_Mut2...]].pdb`.
- Letras griegas transliteradas cuando sea necesario para compatibilidad cross‑platform (ej.: `β` → `beta`), manteniendo el nombre original cuando el sistema de archivos lo permite.
- Mutaciones expresadas con notación estándar: `ResiduoOriginalPosicionResiduoNuevo` (p. ej., `Hh2a_E1A_E4A_Y33W.pdb`).

## Relación con PSF y BD

- Para toxinas con parámetros atómicos, el archivo PSF correspondiente se encuentra en `../psfs/` con el mismo
  nombre base (p. ej., `μ-TRTX-Hh2a.psf` ↔ `μ-TRTX-Hh2a.pdb`).
- Algunos PDB son insertados como BLOB en la base `database/toxins.db` por los loaders de `loaders/`.

## Uso en el pipeline

- Carga y corte: `extractors/cortar_pdb.py` (PDBHandler) y loaders de Nav1.7 (`loaders/insert_Nav1_7_pdbs.py`).
- Análisis de grafos/dipolo: `graphs/graph_analysis2D.py` y `graphs/graph_analysis3D.py`.
- Visualización: interfaz Flask (Mol* / py3Dmol) para overlays de métrica y vector dipolar.

## Lineamientos para agregar nuevos PDB

1. Verificar que corresponde al péptido maduro (o acompañar índices de corte si se requiere recorte).
2. Confirmar conectividad S–S y ausencia de huecos críticos tras el recorte.
3. Mantener convención de nombres y ubicar WT en `WT/` cuando corresponda.
4. Si existe PSF asociado, colocarlo en `../psfs/` y verificar carga conjunta PDB+PSF.
5. Opcional: actualizar la BD con el loader correspondiente.

