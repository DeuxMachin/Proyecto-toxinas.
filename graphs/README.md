# graphs — Análisis de grafos moleculares (2D/3D) y propiedades físico‑químicas

Este módulo implementa la representación y el análisis topológico de toxinas peptídicas a partir de estructuras obtenidas desde PDB/AlphaFold y secuencias/identificadores provenientes de consultas a UniProt junto con las NaV1.7. Cubre desde la construcción de grafos a nivel de residuo (2D) con atributos físico‑químicos y estructurales, hasta la visualización 3D de grafos atómicos.

## Qué resuelve
- Construcción de grafos moleculares a partir de PDB (nodo = residuo, arista = proximidad/peptídica/SS) con umbral configurable.
- Anotación de nodos con propiedades físico‑químicas y estructurales: tipo de residuo, carga, hidrofobicidad, SASA, estructura secundaria, pertenencia a puente disulfuro, etc.
- Cálculo de métricas topológicas (degree, betweenness, closeness, eigenvector, clustering) y motivos estructurales (horquillas β, nudo de cistina, parches de carga/hidrofóbicos).
- Estimación de momento dipolar con y sin PSF (MDAnalysis), incluyendo ángulo respecto del eje Z para usos de visualización.
- Visualizaciones 2D explicativas y 3D interactivas (Plotly/Graphein) exportables a HTML.

## Tecnologías y dependencias clave
- BioPython (Bio.PDB, DSSP, NeighborSearch, PPBuilder) — parsing PDB, DSSP, SASA, vecinos.
- NetworkX — construcción del grafo y métricas de centralidad/comunidades.
- MDAnalysis — lectura de PSF y cálculo de dipolo con cargas atomísticas cuando hay PSF.
- NumPy/SciPy — geometría, distancias, estadística básica.
- Matplotlib/Seaborn — visualización 2D y heatmaps de métricas.
- Graphein + Plotly — grafo atómico 3D interactivo exportable a HTML.

Nota: Para DSSP se requiere el binario `mkdssp` disponible en el sistema. Si no está instalado, el cálculo de estructura secundaria y SASA fallará de forma segura y el análisis continuará sin esos atributos.

## Arquitectura y lógica

### 1) Grafos 2D a nivel de residuo — `graph_analysis2D.py`
- Clase principal: `Nav17ToxinGraphAnalyzer(pdb_folder="pdbs/")`
- Contrato de funciones principales (inputs/outputs):
  - `load_pdb(pdb_filename) -> Bio.PDB.Structure`: carga la estructura.
  - `calculate_secondary_structure(structure) -> (dict residue_ss, dict sasa)` usando DSSP.
  - `find_disulfide_bridges(structure) -> list[(res_i, res_j)]` detecta puentes S–S por distancia SG–SG.
  - `calculate_dipole_moment(structure) -> dict` dipolo por cargas simplificadas a nivel de residuo (CA).
  - `calculate_dipole_moment_with_psf(pdb_path, psf_path=None) -> dict` dipolo usando PSF (MDAnalysis) si existe; si no, método de respaldo por BioPython.
  - `build_enhanced_graph(structure, cutoff_distance=8.0, pharmacophore_pattern=None) -> nx.Graph` construye el grafo con nodos y aristas anotadas.
  - `calculate_graph_metrics(G) -> dict` métricas globales y promedios por centralidades.
  - `detect_structural_motifs(G) -> dict` heurísticas de motivos (β‑hairpin, nudo de cistina, parches positivos/hidrofóbicos).
  - `visualize_enhanced_graph(G, ...) -> None` render 2D con leyendas y anotaciones.
  - `visualize_centrality_metrics(result) / plot_centrality_metrics(result)` tablas y gráficos de centralidades.
  - `analyze_single_toxin(pdb_filename, cutoff_distance=8.0, plot_3d=False, pharmacophore_pattern=None) -> dict` pipeline de análisis y visualización “one‑shot”.

- Modelo del grafo (resumen):
  - Nodo = residuo (CA), id = número de residuo PDB.
  - Atributos de nodo: `amino_acid`, `name`, `pos` (3D), `pos_2d`, `hydrophobicity`, `charge`, `residue_type` (hidrofóbico/polar/±/Cys), `secondary_structure`, `is_in_disulfide`, `sasa`, `is_surface`, `is_pharmacophore`, `pharmacophore_part`, centralidades.
  - Aristas: `type ∈ {distance, peptide, disulfide}` con `weight` y `interaction_strength` (heurístico).
  - Atributos globales: `dipole_vector`, `dipole_magnitude`, `disulfide_count`.

- Farmacóforo: `identify_pharmacophore_residues` permite resaltar fragmentos de secuencia (p. ej., “WF–S–WCKY”). Se mapea sobre la secuencia derivada del orden de nodos.

- Motivos: detección heurística basada en etiquetas de estructura secundaria y proximidad espacial de conjuntos de residuos.

### 2) Grafo 3D a nivel atómico — `graph_analysis3D.py`
- Usa Graphein para construir un grafo atómico con enlaces covalentes reales (`add_atomic_edges`) a partir de un PDB local.
- Visualiza con `plotly_protein_structure_graph` y guarda `protein_3d_view.html`.
- Parámetros clave: `granularity="atom"`, `pdb_dir="pdbs/"`, `path=PDB_FILE`.

## Requisitos previos
- PDBs en `pdbs/` con nombres coherentes con las toxinas.
- Para DSSP: binario `mkdssp` disponible en PATH del sistema (o vía conda). Si no, el análisis continúa sin SS/SASA.
- Para dipolo con PSF: archivos `.psf` en `psfs/` y MDAnalysis instalado.
- Dependencias listadas en `requirements.txt`.

## Uso rápido (Windows PowerShell)

- Análisis 2D de una toxina concreta con visualización y métricas:

```powershell
python -c "from graphs.graph_analysis2D import Nav17ToxinGraphAnalyzer; a=Nav17ToxinGraphAnalyzer('pdbs/'); a.analyze_single_toxin('β-TRTX-Cd1a.pdb', cutoff_distance=8.0, pharmacophore_pattern='WF–S–WCKY')"
```

- Visualización 3D atómica con Graphein/Plotly (exporta HTML):

```powershell
python graphs/graph_analysis3D.py
```

El HTML `protein_3d_view.html` quedará en la raíz del proyecto, abrible con el navegador.

## Resultados y artefactos
- Consola: resumen de métricas y motivos; listados de residuos top por centralidades.
- Ventana Matplotlib: grafo 2D con leyenda rica y etiquetas (#:AA, símbolos de SS, superficie, farmacóforo).
- HTML 3D: exploración interactiva de la topología atómica.

## Consideraciones y edge cases
- PDBs con residuos no estándar o sin átomos CA: serán ignorados en algunas etapas (se informa en consola).
- DSSP no disponible: `secondary_structure` y `sasa` quedarán vacíos; los motivos que dependen de SS pueden no detectarse.
- PSF ausente: el dipolo usa un esquema simplificado de cargas por residuo (útil como proxy, no como valor cuantitativo absoluto).
- Numeración de residuos discontinua: las aristas “peptide” sólo se añaden cuando id_n+1 == id_n + 1.

## Extensiones futuras
- Umbrales adaptativos por tipo de contacto (H‑bond, π‑stacking) y aristas anotadas por tipo de interacción.
- Carga de farmacóforos desde configuración/BD y matching por reglas de patrón más expresivas.
- Exportación de métricas a Excel para trazabilidad (graph_metrics.xlsx, graph_edges.xlsx).

---
