# 📋 **INICIALIZACIÓN DEL PROYECTO - ANÁLISIS DE TOXINAS NAV1.7**

## 🔄 **SECUENCIA DE EJECUCIÓN Y RELACIONES ENTRE SCRIPTS**

El proyecto sigue una secuencia específica de scripts que construyen progresivamente la base de datos de toxinas Nav1.7. Cada script tiene dependencias del anterior y cumple una función específica en el pipeline de datos.

---

## **FASE 1: INICIALIZACIÓN** - `create_db.py`

### **🎯 Propósito:**
Crea la estructura inicial de la base de datos SQLite con todas las tablas necesarias.

### **📊 Tablas creadas:**
- `Proteins` - Información general de proteínas de UniProt
- `ProteinShortNames` - Nombres cortos alternativos
- `ProteinAlternativeNames` - Nombres alternativos completos  
- `Peptides` - Péptidos extraídos con estructuras PDB/AlphaFold
- `Nav1_7_InhibitorPeptides` - Datos específicos de inhibidores Nav1.7

### **🔗 Salida:**
Base de datos vacía `database/toxins.db` lista para recibir datos.

**📝 Comando de ejecución:**
```bash
python database/create_db.py
```

---

## **FASE 2: RECOLECCIÓN DE PROTEÍNAS** - `extractors/uniprot.py`

### **🎯 Propósito:**
**Búsqueda y descarga masiva de proteínas desde UniProt** basada en queries específicas (ej: "knottin AND venom").

### **🔧 Funcionalidades detalladas:**

#### **Clase `UniProtPipeline`:**

**1. `fetch_accessions(query)`:**
- Consulta la API REST de UniProt: `https://rest.uniprot.org/uniprotkb/search`
- Parámetros: `query`, `format=json`, `size=500`, `fields=accession`
- **Resultado**: Lista de `accession numbers` (ej: P83303, P84507)
- **Archivo generado**: `data/processed/{query}_accessions.json`

**2. `fetch_all_async(accessions)`:**
- Descarga concurrente (máx. 20 simultáneas) de datos XML por cada accession
- URL por proteína: `https://rest.uniprot.org/uniprotkb/{accession}.xml`
- **Manejo de errores**: Reintentos automáticos, timeout 60s, manejo de rate limits

**3. `parse_protein(xml_content)`:**
- Extrae del XML: nombre, organismo, gen, descripción, secuencia, longitud
- **Características clave**: `features` tipo `peptide`/`chain`, estructuras `PDB`/`AlphaFoldDB`
- **Datos estructurales**: IDs PDB, enlaces AlphaFold, información de cadenas

**4. Almacenamiento dual:**
- **XML legible**: `data/processed/{query}_data.xml` con formato pretty-print
- **Base de datos**: Inserción en tablas `Proteins`, `ProteinShortNames`, `ProteinAlternativeNames`

### **🔗 Entrada:**
Query de búsqueda (ej: "knottin AND venom", "spider toxin Nav1.7")

### **🔗 Salida:**
- Archivo XML con proteínas completas
- BD poblada con información básica de proteínas
- **Sin estructuras PDB aún - solo metadatos**

**📝 Comando de ejecución:**
```bash
python extractors/uniprot.py
# Solicita interactivamente el query de búsqueda
```

---

## **FASE 3: EXTRACCIÓN DE PÉPTIDOS** - `extractors/peptide_extractor.py`

### **🎯 Propósito:**
**Procesamiento inteligente de péptidos**: descarga estructuras PDB/AlphaFold, corta según rangos de residuos y almacena péptidos funcionales.

### **🔧 Funcionalidades detalladas:**

#### **Clase `PeptideExtractor`:**

**1. `extract_peptides_from_xml(xml_path)`:**
- **Lógica diferenciada por tipo de estructura:**
  
  **Para estructuras PDB:**
  - Utiliza rangos específicos de cadenas PDB (ej: "A=46-72")
  - Prioriza el rango más largo disponible
  - **Ventaja**: Precisión basada en estructura cristalográfica real
  
  **Para estructuras AlphaFold:**
  - Aplica lógica de péptidos superpuestos vs separados
  - **Péptidos superpuestos**: Selecciona el más largo
  - **Péptidos separados**: Crea múltiples cortes (CUT 1/N, CUT 2/N)

**2. `download_pdb_file(pdb_id)`:**
- **Estrategia de descarga por prioridad:**
  1. Archivo local existente (cache)
  2. RCSB PDB: `https://files.rcsb.org/download/{pdb_id}.pdb` (IDs de 4 caracteres)
  3. AlphaFold: `https://alphafold.ebi.ac.uk/files/AF-{id}-F1-model_v4.pdb`
  4. Modelos alternativos: F2, F3 versions
- **Gestión de archivos**: Almacenamiento en `data/pdb_raw`

**3. `process_peptide(peptide)` + Integración con `extractors/cortar_pdb.py`:**
- **Corte inteligente usando `PDBHandler.cut_pdb_by_residue_indices()`**
- **Estrategias de fallback:**
  1. Corte exacto según coordenadas de péptido
  2. Ajuste de rangos si están fuera de límites
  3. **Estructura completa** si el corte falla (marca `is_full_structure=True`)
- **Contenido final**: Archivo PDB recortado almacenado como BLOB

**4. `save_peptide_to_db(peptide)`:**
- Inserción en tabla `Peptides` con todos los metadatos:
  - `accession_number`, `peptide_name`, `start_position`, `end_position`
  - `sequence`, `model_source` (PDB/AlphaFoldDB), `model_id`, `model_link`
  - `pdb_file` (contenido binario), `is_full_structure` (boolean)

### **🔗 Entrada:**
Archivo XML de `extractors/uniprot.py` con proteínas y estructuras asociadas

### **🔗 Salida:**
- Tabla `Peptides` poblada con péptidos funcionales
- Estructuras PDB descargadas y cortadas según rangos biológicos
- **Cache local** de estructuras en `data/pdb_raw`

**📝 Comando de ejecución:**
```bash
python extractors/peptide_extractor.py
# Procesa archivos XML existentes en data/processed/
```

---

## **FASE 4: DATOS ESPECÍFICOS NAV1.7** - `loaders/instert_Nav1_7.py`

### **🎯 Propósito:**
**Inserción de datos experimentales específicos** de inhibidores Nav1.7 con información farmacológica curada manualmente.

### **🔧 Funcionalidades:**

#### **Dataset curado manualmente:**
```python
peptides_data = [
    {
        "accession_number": "P83303",
        "peptide_code": "μ-TRTX-Hh2a", 
        "sequence": "ECLEIFKACNPSNDQCCKSSKLVCSRKTRWCKYQI",
        "pharmacophore_match": "IF–S–WCKY",
        "residue_count": 7,
        "ic50": 17.0,
        "unit": "nM",
        "pdb_download_link": "https://files.rcsb.org/download/1MB6.pdb"
    },
    # ... 22 péptidos más con mutantes y wild-types
]
```

#### **Datos únicos incluidos:**
- **Códigos de nomenclatura**: μ-TRTX-Hh2a, β-TRTX-Cd1a, ω-TRTX-Gr2a
- **Datos farmacológicos**: IC50 values y unidades (nM, μM)
- **Análisis de farmacóforos**: Patrones de residuos clave (ej: "IF–S–WCKY")
- **Mutantes específicos**: E1A, E4A, Y33W, variantes combinadas
- **Enlaces directos**: URLs específicas a estructuras PDB/AlphaFold

### **🔗 Entrada:**
Dataset hardcodeado extraído de literatura científica

### **🔗 Salida:**
Tabla `Nav1_7_InhibitorPeptides` poblada con 23 péptidos especializados

**📝 Comando de ejecución:**
```bash
python loaders/instert_Nav1_7.py
```

---

## **FASE 5: ESTRUCTURAS PDB LOCALES** - `loaders/insert_Nav1_7_pdbs.py`

### **🎯 Propósito:**
**Procesamiento de archivos PDB locales** para péptidos Nav1.7, con corte automático basado en secuencias.

### **🔧 Funcionalidades detalladas:**

#### **Clase `PDBCutterInserter`:**

**1. `fetch_peptides()`:**
- Query: `SELECT peptide_code, sequence FROM Nav1_7_InhibitorPeptides`
- Obtiene lista de péptidos que necesitan estructuras PDB

**2. `find_pdb_file(peptide_code)`:**
- Busca archivos locales: `pdbs/{peptide_code}.pdb`
- **Convención de nombres**: Archivos deben coincidir exactamente con `peptide_code`

**3. `cut_pdb_if_needed(pdb_path, expected_sequence)` + `PDBHandler`:**
- **Extracción de secuencia**: `PDBHandler.extract_primary_sequence(pdb_path)`
- **Búsqueda de coincidencia**: Localiza `expected_sequence` dentro de la secuencia PDB
- **Corte preciso**: 
  ```python
  start_index = pdb_sequence.index(expected_sequence) + 1
  end_index = start_index + len(expected_sequence) - 1
  PDBHandler.cut_pdb_by_residue_indices(pdb_path, cut_pdb_path, start_index, end_index)
  ```
- **Fallback**: Si no hay coincidencia exacta, guarda estructura completa

**4. `update_pdb_in_database()`:**
- Query: `UPDATE Nav1_7_InhibitorPeptides SET pdb_blob = ? WHERE peptide_code = ?`
- Almacena contenido PDB como BLOB binario

### **🔗 Entrada:**
- Tabla `Nav1_7_InhibitorPeptides` con péptidos registrados
- Archivos PDB locales en `pdbs/` con nomenclatura específica

### **🔗 Salida:**
Campo `pdb_blob` poblado con estructuras PDB cortadas específicamente

**📝 Comando de ejecución:**
```bash
python loaders/insert_Nav1_7_pdbs.py
```

**⚠️ Prerequisitos:**
- Archivos PDB en carpeta `pdbs/` con nombres exactos: `{peptide_code}.pdb`

---

## **FASE 6: ARCHIVOS PDB + PSF COMPLETOS** - `loaders/new_instert_Nav1_7_pdb_psf.py`

### **🎯 Propósito:**
**Inserción masiva de archivos PDB y PSF** para simulaciones moleculares completas.

### **🔧 Funcionalidades detalladas:**

#### **Clase `PDBAndPSFInserter`:**

**1. Sistema de archivos dual:**
- **Carpeta PDB**: `pdbs/` con archivos `.pdb`
- **Carpeta PSF**: `psfs/` con archivos `.psf` (parámetros CHARMM/NAMD)

**2. `read_file_as_blob(folder, filename, extension)`:**
- Lectura binaria: `open(path, "rb")`
- **Manejo de ausencias**: Retorna `None` si archivo no existe
- **Flexibilidad**: Permite archivos PDB sin PSF o viceversa

**3. `update_blobs_in_database()`:**
- Query dual: `UPDATE Nav1_7_InhibitorPeptides SET pdb_blob = ?, psf_blob = ? WHERE peptide_code = ?`
- **Actualización simultánea** de ambos campos BLOB

**4. `process_all_peptides()`:**
- **Iteración completa** sobre todos los `peptide_code` en BD
- **Búsqueda por convención**: `{peptide_code}.pdb` y `{peptide_code}.psf`
- **Logging detallado**: Estado de cada archivo encontrado/faltante

### **🔗 Entrada:**
- Archivos locales organizados: `pdbs/*.pdb` y `psfs/*.psf`
- Tabla `Nav1_7_InhibitorPeptides` existente

### **🔗 Salida:**
Campos `pdb_blob` y `psf_blob` completamente poblados para simulaciones moleculares

**📝 Comando de ejecución:**
```bash
python loaders/new_instert_Nav1_7_pdb_psf.py
```

**⚠️ Prerequisitos:**
- Archivos en `pdbs/{peptide_code}.pdb`
- Archivos en `psfs/{peptide_code}.psf` (opcionales)

---

## **🔄 DEPENDENCIAS Y FLUJO DE DATOS**

### **Relaciones entre scripts:**

```
create_db.py
    ↓
uniprot.py
    ↓
peptide_extractor.py
    ↓
instert_Nav1_7.py
    ↓
insert_Nav1_7_pdbs.py
    ↓
new_instert_Nav1_7_pdb_psf.py
```

### **Datos acumulativos por fase:**

| Fase | Script | Tabla Principal | Datos Añadidos | Dependencias |
|------|--------|----------------|-----------------|--------------|
| 1 | `create_db.py` | Todas | Estructura BD | - |
| 2 | `uniprot.py` | `Proteins` | Metadatos UniProt | Fase 1 |
| 3 | `peptide_extractor.py` | `Peptides` | Estructuras PDB cortadas | Fase 2 |
| 4 | `instert_Nav1_7.py` | `Nav1_7_InhibitorPeptides` | Datos experimentales | Fase 1 |
| 5 | `insert_Nav1_7_pdbs.py` | `Nav1_7_InhibitorPeptides` | `pdb_blob` cortado | Fase 4 |
| 6 | `new_instert_Nav1_7_pdb_psf.py` | `Nav1_7_InhibitorPeptides` | `pdb_blob` + `psf_blob` | Fase 5 |

### **Archivos auxiliares críticos:**

- **`extractors/cortar_pdb.py`**: Módulo compartido para operaciones de corte PDB usando MDAnalysis
- **`data/pdb_raw/`**: Cache de estructuras descargadas
- **`pdbs/` y `psfs/`**: Archivos locales organizados por nomenclatura

---

## **📋 CHECKLIST DE EJECUCIÓN COMPLETA**

### **⚙️ Preparación del entorno:**
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear estructura de directorios
mkdir -p data/pdb_raw data/processed pdbs psfs database
```

### **🚀 Secuencia de ejecución:**
```bash
# FASE 1: Crear base de datos
python database/create_db.py

# FASE 2: Descargar proteínas de UniProt
python extractors/uniprot.py
# → Introduce query: "knottin AND venom"

# FASE 3: Extraer y procesar péptidos
python extractors/peptide_extractor.py

# FASE 4: Insertar datos Nav1.7 específicos
python loaders/instert_Nav1_7.py

# FASE 5: Procesar PDBs locales (opcional)
python loaders/insert_Nav1_7_pdbs.py

# FASE 6: Insertar PDBs y PSFs completos
python loaders/new_instert_Nav1_7_pdb_psf.py
```

### **✅ Verificación de éxito:**
```sql
-- Verificar datos en SQLite
.open database/toxins.db
.tables
SELECT COUNT(*) FROM Proteins;
SELECT COUNT(*) FROM Peptides;
SELECT COUNT(*) FROM Nav1_7_InhibitorPeptides;
SELECT peptide_code, LENGTH(pdb_blob), LENGTH(psf_blob) FROM Nav1_7_InhibitorPeptides LIMIT 5;
```

---

## **🎯 RESULTADO FINAL**

Al completar toda la secuencia, el proyecto dispone de:

1. **Base de datos completa** con proteínas, péptidos y estructuras
2. **Datos experimentales curados** específicos para Nav1.7
3. **Estructuras PDB optimizadas** cortadas según regiones funcionales
4. **Archivos PSF** para simulaciones moleculares avanzadas
5. **Sistema de cache** para evitar re-descargas
6. **Trazabilidad completa** desde UniProt hasta estructuras finales

Esta arquitectura permite análisis posteriores de grafos moleculares, cálculos de momento dipolar, y exportación de datos para investigación farmacológica de inhibidores Nav1.7.

---

## **🐛 TROUBLESHOOTING**

### **Errores comunes:**

**Error: "No such table: Proteins"**
- **Solución**: Ejecutar `python database/create_db.py` primero

**Error: "No se encontró PDB para {peptide_code}"**
- **Solución**: Verificar que archivos PDB estén en `pdbs/` con nombres exactos

**Error: "ConnectionError al descargar de UniProt"**
- **Solución**: Verificar conexión a internet y reintentar

**Error: "ModuleNotFoundError: No module named 'MDAnalysis'"**
- **Solución**: `pip install MDAnalysis`

### **Archivos de log:**
- Todos los scripts generan output detallado en consola
- Errores específicos se muestran con contexto completo
- Para debugging: agregar prints adicionales en puntos críticos

---

*📅 Documento generado: Agosto 2025*  
*🔧 Proyecto: Análisis de Toxinas Nav1.7 con Grafos Moleculares*
