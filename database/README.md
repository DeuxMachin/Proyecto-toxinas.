# database — Esquema y creación de la base de datos SQLite

Esta carpeta define y materializa el esquema persistente central (`toxins.db`) que almacena:
- Proteínas base provenientes de UniProt (identificadores, nombres, secuencia, metadatos).
- Alias/nombres alternativos.
- Péptidos derivados (sub‑secuencias, cortes, fragmentos modelados) y su PDB en texto (BLOB opcional).
- Péptidos inhibidores Nav1.7 con anotaciones farmacóforo, IC50 y blobs binarios PDB/PSF + grafos pre-calculados.

## Archivos
| Archivo | Descripción |
|---------|-------------|
| `create_db.py` | Script idempotente que crea (si no existe) el archivo `toxins.db` y las tablas fundamentales. |
| `toxins.db` | Base de datos SQLite resultante (binario). |

## Esquema (tablas)

### 1. `Proteins`
Campos clave:
- `accession_number` (PK): ID primario de UniProt.
- `name`, `full_name`, `organism`, `gene`, `description`: metadatos descriptivos.
- `sequence`, `length`: secuencia completa y longitud declarada.

Uso: Origen para derivar cortes de péptidos y relacionarlos con estructuras PDB/AlphaFold.

### 2. `ProteinShortNames`
Alias cortos (siglas) asociados a un `accession_number`.

### 3. `ProteinAlternativeNames`
Nombres alternativos extendidos. Se separan para permitir cardinalidad N.

### 4. `Peptides`
Fragmentos o péptidos anotados (features `peptide` o `chain`):
- `peptide_name`: descripción del feature.
- `start_position`, `end_position`: rango en la secuencia completa.
- `model_source` (`PDB` | `AlphaFold` | NULL) + `model_id` y `model_link`.
- `pdb_file` (BLOB texto): contenido PDB recortado o completo.
- `is_full_structure`: flag (0/1) si el rango no pudo recortarse y se almacena la estructura completa.

### 5. `Nav1_7_InhibitorPeptides`
Colección curada de péptidos inhibidores Nav1.7 con datos experimentales:
- `pharmacophore_match`, `pharmacophore_residue_count`.
- `ic50_value`, `ic50_unit` (ej. nM, µM).
- `pdb_blob`, `psf_blob`: binarios de estructura y topología.
- `graph_full_structure`, `graph_beta_hairpin`, `graph_hydrophobic_patch`, `graph_charge_ring`: slots para grafos específicos precalculados (optimización futura de acceso).

## Flujo de Creación
1. Ejecutar `python database/create_db.py` (idempotente: usa `CREATE TABLE IF NOT EXISTS`).
2. Poblar tablas con scripts de ingestión:
   - UniProt (`extractors/uniprot.py` + `extractors/peptide_extractor.py`).
   - Carga manual/Nav1.7 (`loaders/instert_Nav1_7*.py`).
3. Adjuntar blobs PDB/PSF y grafos a medida que el pipeline de análisis los produce.

## Relaciones Lógicas
- `ProteinShortNames.accession_number` → `Proteins.accession_number` (FK implícita).
- `ProteinAlternativeNames.accession_number` → idem.
- `Peptides.accession_number` → Proteína madre.
- `Nav1_7_InhibitorPeptides.accession_number` → Proteína fuente (no estrictamente necesaria para algunos flujos, pero útil para trazabilidad).


## Consideraciones y Edge Cases
- Longitudes: Validar que `start_position/end_position` calzan dentro de `Proteins.sequence` (el extractor ya intenta corregir). 
- Unicode: Nombres de péptidos con caracteres griegos se preservan (SQLite soporta UTF‑8). 
- Blobs grandes: Para PDB/PSF muy extensos, considerar almacenamiento en filesystem + path en DB (optimización futura). 
- Integridad referencial: FKs no están definidas con `ON DELETE CASCADE`; borrar una proteína puede dejar huérfanos si no se maneja manualmente. 


## Uso Rápido
```bash
python database/create_db.py
```
Salida esperada:
```
[✓] Base de datos creada en: database/toxins.db
```
