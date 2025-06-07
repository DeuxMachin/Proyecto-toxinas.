# Proyecto Toxinas - Análisis de Toxinas Nav1.7

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Mol*](https://img.shields.io/badge/Mol*-Latest-orange.svg)](https://molstar.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Latest-red.svg)](https://networkx.org/)

Un proyecto de análisis computacional para estudiar Toxinas que interactúan con canales de sodio Nav1.7, utilizando análisis de grafos moleculares y visualización 3D interactiva con métricas de centralidad avanzadas.

## 🧬 Descripción

Este proyecto proporciona herramientas para analizar la estructura y propiedades de péptidos tóxicos que se dirigen específicamente a los canales de sodio Nav1.7. Combina análisis de grafos moleculares con visualización 3D interactiva para identificar residuos críticos y patrones estructurales.

### Características Principales

- **Análisis de Centralidad**: Cálculo de métricas de centralidad (betweenness, closeness, degree) para identificar residuos importantes
- **Visualización 3D**: Integración completa con Molstar para visualización molecular interactiva
- **Exportación de Datos**: Funcionalidad completa de exportación CSV con todas las métricas de residuos
- **Base de Datos**: Sistema de almacenamiento SQLite para gestión eficiente de estructuras PDB
- **Análisis de IC50**:  Integración de datos de actividad biológica; todos los valores se convierten a nM para permitir análisis comparativos de actividad  

- **Correlación Estructura-Actividad**: Análisis combinado de métricas estructurales y datos IC50

## 🚀 Instalación Rápida

### Prerrequisitos

- Python 3.8+
- pip (gestor de paquetes de Python)

### Configuración del Entorno

1. **Clonar el repositorio**:
```bash
git clone https://github.com/tuusuario/Proyecto-toxinas.git
cd Proyecto-toxinas
```

2. **Crear entorno virtual**:
```bash
python -m venv toxinas
# Windows
toxinas\Scripts\activate
# Linux/Mac
source toxinas/bin/activate
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar la base de datos**:
```bash
python database/create_db.py
python database/pdb_data_insert.py
```

5. **Ejecutar la aplicación**:
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

## 📋 Dependencias Principales

```txt
flask>=2.0.0
numpy>=1.21.0
pandas>=1.3.0
networkx>=2.6
biopython>=1.79
matplotlib>=3.4.0
seaborn>=0.11.0
plotly>=5.0.0
sqlite3
requests>=2.26.0
graphein>=1.7.0
```

## 🛠 Uso Detallado

### Interfaz Web Principal

1. **Acceder al Dashboard**: Navega a `http://localhost:5000`
2. **Seleccionar Péptido**: Elige un péptido de la lista desplegable (fuente: toxinas/nav1_7)
3. **Configurar Parámetros**:
   - **Granularidad**: `CA` (residuos) o `Atom` (atómico)
   - **Distancia Umbral**: 6.0-12.0 Å (recomendado: 8.0-10.0 Å)
   - **Separación Secuencial**: 3-10 residuos (recomendado: 5)
4. **Visualizar Estructura**: La estructura 3D se carga automáticamente con Molstar
5. **Analizar Métricas**: Revisa las métricas de centralidad en el panel lateral
6. **Exportar Datos**: Utiliza el botón "Exportar Datos CSV" para descargar todos los datos

### Análisis de Centralidad Implementado

El sistema calcula automáticamente las siguientes métricas:

- **Degree Centrality**: Número de conexiones directas de cada residuo
- **Betweenness Centrality**: Identifica residuos que actúan como "puentes" en la estructura
- **Closeness Centrality**: Mide qué tan "cerca" está un residuo de todos los demás







## 📊 Estructura de Base de Datos

### Tablas Principales

#### `peptides`
- **Función**: Almacena información estructural de péptidos
- **Campos clave**: `id`, `name`, `source`, `pdb_content`, `sequence`

#### `Nav1_7_InhibitorPeptides` 
- **Función**: Datos de actividad biológica y clasificación
- **Campos clave**: 
  - `peptide_name`: Nombre del péptido/toxina
  - `ic50_value`: Valor de concentración inhibitoria 50%
  - `ic50_unit`: Unidad de medida (μM, nM, mM)
  - `classification`: Familia de toxina (ej: μ-TRTX-Hd1a)

#### Integración de Datos
- **Normalización IC50**: Conversión automática a nM para análisis consistente
- **Clasificación por familias**: Consultas SQL optimizadas para agrupar subfamilias
- **Correlación estructural**: Join entre métricas topológicas y datos de actividad

### Consultas Ejemplo

#### Obtener familia μ-TRTX-H:
```sql
SELECT DISTINCT peptide_name FROM Nav1_7_InhibitorPeptides 
WHERE peptide_name LIKE 'μ-TRTX-%2a' OR peptide_name LIKE 'mu-TRTX-%2a'
```

#### Normalización IC50:
```sql
CASE 
    WHEN ic50_unit = 'μM' THEN ic50_value * 1000
    WHEN ic50_unit = 'mM' THEN ic50_value * 1000000
    ELSE ic50_value 
END as normalized_ic50_nm
```

## 📁 Estructura del Proyecto

```
proyecto-toxinas/
├── app/                          # Aplicación Flask principal
│   ├── routes/                   # Rutas de la API
│   │   └── viewer_routes.py      # Endpoints para visualización
│   ├── static/                   # Archivos estáticos
│   │   ├── css/                  # Estilos CSS
│   │   └── js/                   # JavaScript frontend
│   │       ├── molstar_analyzer.js    # Análisis con Mol*
│   │       ├── graph_viewer.js         # Visualización de grafos
│   │       └── viewer.js               # Control principal
│   ├── templates/                # Templates HTML
│   │   └── viewer.html           # Interface principal
│   └── __init__.py              # Inicialización de Flask
├── database/                     # Gestión de base de datos
│   ├── create_db.py             # Creación de esquema
│   ├── pdb_data_insert.py       # Inserción de datos
│   └── toxins.db                # Base de datos SQLite
├── extractors/                   # Herramientas de extracción
│   ├── cortar_pdb.py            # Manipulación de archivos PDB
│   ├── peptide_extractor.py     # Extracción de péptidos
│   └── uniprot.py               # API de UniProt
├── graphs/                       # Análisis de grafos
│   ├── graph_analysis2D.py      # Análisis 2D de grafos
│   ├── graph_analysis3D.py      # Análisis 3D de grafos
│   └── graph2.py                # Herramientas adicionales
├── loaders/                      # Cargadores de datos
├── pdbs/                         # Archivos PDB almacenados
├── data/                         # Datos de entrenamiento y procesados
│   ├── pdb_raw/                 # Archivos PDB sin procesar
│   └── processed/               # Datos procesados
├── tests/                        # Tests y ejemplos
├── requirements.txt              # Dependencias Python
├── config.py                    # Configuración
└── run.py                       # Punto de entrada
```

## 🎯 Uso de la Aplicación

### 1. Cargar Datos de Proteínas

#### Desde UniProt
```python
from extractors.uniprot import UniProtPipeline

pipeline = UniProtPipeline()
# Buscar toxinas relacionadas con Nav1.7
accessions, prefix = pipeline.fetch_accessions("Nav1.7 toxin")
```

#### Desde archivos PDB locales
```python
from extractors.cortar_pdb import PDBHandler

# Extraer secuencia de un PDB
sequence = PDBHandler.extract_primary_sequence("archivo.pdb")

# Recortar PDB por rango de residuos
PDBHandler.cut_pdb_by_residue_range("input.pdb", "output.pdb", 1, 50)
```

### 2. Análisis de Grafos Moleculares

#### Análisis básico
```python
from graphs.graph_analysis2D import Nav17ToxinGraphAnalyzer

analyzer = Nav17ToxinGraphAnalyzer()
result = analyzer.analyze_single_toxin("toxina.pdb", cutoff_distance=8.0)

print(f"Nodos: {result['graph_properties']['num_nodes']}")
print(f"Densidad: {result['graph_properties']['density']:.4f}")
```

#### Métricas de centralidad
```python
# Obtener residuos con mayor centralidad
degree_top = result['centrality_measures']['degree_centrality_more']
betweenness_top = result['centrality_measures']['betweenness_centrality_more']

print(f"Residuos clave (grado): {degree_top}")
print(f"Residuos clave (intermediación): {betweenness_top}")
```

### 3. Interface Web

#### Navegación por pestañas
- **Pestaña Principal**: Visualización 3D con Mol*
- **Pestaña Grafos**: Análisis de redes moleculares con métricas

#### Controles interactivos
- **Granularidad**: Alternar entre vista atómica y de residuos
- **Distancia umbral**: Ajustar conexiones del grafo (Å)
- **Separación de secuencia**: Filtrar conexiones por distancia secuencial

#### Exportación de datos
- **CSV completo**: Descargar métricas de todos los residuos
- **Análisis detallado**: Top 5 residuos por métrica de centralidad

## 🔧 API Endpoints

### Visualización de Proteínas
```http
GET /get_pdb/<source>/<id>
```
Obtiene datos PDB de una proteína específica.

### Análisis de Grafos
```http
GET /get_protein_graph/<source>/<id>?long=5&threshold=10.0&granularity=CA
```
Genera y analiza el grafo molecular con parámetros personalizables.

### Exportación de Datos
```http
GET /export_residues_csv/<source>/<id>?long=5&threshold=10.0&granularity=CA
```
Exporta métricas completas en formato CSV para un péptido individual.

### Exportación por Familias
```http
GET /export_family_csv/<family_name>
```
Exporta datos completos de una familia específica de toxinas con integración IC50.
- **Parámetros soportados**: 
  - `family_name`: Nombre de la familia (ej: "μ-TRTX-H", "μ-TRTX-C", "κ-TRTX")
- **Formato de respuesta**: Archivo CSV con datos combinados de estructura y actividad
- **Características**: Normalización automática de IC50, diferenciación de subfamilias

## 🧪 Análisis Científico

### Métricas de Centralidad Implementadas

1. **Centralidad de Grado**: Identifica residuos con mayor número de conexiones
2. **Centralidad de Intermediación**: Detecta residuos que actúan como "puentes"
3. **Centralidad de Cercanía**: Encuentra residuos centrales en la estructura
4. **Coeficiente de Agrupamiento**: Mide la densidad local de conexiones

### Aplicaciones Específicas para Nav1.7

- **Identificación de farmacóforos**: Residuos clave para interacción
- **Análisis de puentes disulfuro**: Estabilidad estructural
- **Mapeo de superficies de interacción**: Regiones de unión al canal
- **Clasificación de toxinas**: Por patrones estructurales

### Análisis de Relación Estructura-Actividad (SAR)

#### Integración de Datos IC50
- **Base de datos integrada**: Tabla `Nav1_7_InhibitorPeptides` con datos de actividad
- **Normalización automática**: Conversión de μM y mM a nM para análisis consistente
- **Correlación estructural**: Análisis combinado de métricas de centralidad con actividad biológica

#### Clasificación de Familias de Toxinas
- **μ-TRTX Subfamilias**: 
  - **μ-TRTX-H** (terminación 2a): Subfamilia con terminación específica
  - **μ-TRTX-C** (terminación 2b): Subfamilia alternativa
- **κ-TRTX**: Familia adicional de toxinas 
- **Otros grupos**: Extensible para nuevas clasificaciones

#### Metodología de Análisis
1. **Extracción de características**: Métricas topológicas del grafo molecular
2. **Integración de bioactividad**: Datos IC50 experimentales
3. **Análisis comparativo**: Comparación entre familias y subfamilias
4. **Identificación de patrones**: Correlaciones estructura-actividad

## 🎮 Guía de Uso Rápido

### Paso 1: Iniciar la aplicación
```powershell
python run.py
```

### Paso 2: Abrir el navegador
Navegar a `http://localhost:5000`

### Paso 3: Seleccionar una toxina
- Usar los selectores en la interfaz para elegir una proteína
- Las opciones incluyen datos de "toxinas" y "nav1_7"

### Paso 4: Configurar parámetros
- **Distancia umbral**: 6.0-12.0 Å (recomendado: 8.0 Å)
- **Granularidad**: CA (residuos) o Atom (atómico)
- **Separación**: 3-10 residuos (recomendado: 5)

### Paso 5: Analizar resultados
- Revisar métricas de centralidad en el panel derecho
- Examinar el grafo 3D interactivo
- Exportar datos completos en CSV si es necesario

## 🔬 Análisis Avanzado por Familias

### Funcionalidad de Exportación por Familias

La aplicación ahora incluye un sistema avanzado para el análisis comparativo de familias de toxinas:

#### Características Principales
- **Selector de Familia**: Interfaz intuitiva para seleccionar familias específicas
- **Exportación Masiva**: Descarga completa de datasets por familia
- **Análisis SAR**: Correlación estructura-actividad con datos IC50 integrados

#### Familias Soportadas
1. **μ-TRTX-H (mu-TRTX-H)**: Subfamilia con terminación 2a
2. **μ-TRTX-C (mu-TRTX-C)**: Subfamilia con terminación 2b  
3. **κ-TRTX (kappa-TRTX)**: Familia kappa de toxinas
4. **Otras familias**: Extensible para nuevas clasificaciones

#### Uso del Sistema de Familias

1. **Acceder a la sección**: Localizar el panel "Exportar por Familia" en la interfaz
2. **Seleccionar familia**: Usar el menú desplegable para elegir la familia de interés
3. **Exportar datos**: Hacer clic en "Exportar Familia" para descargar el CSV
4. **Analizar resultados**: El archivo incluye todas las métricas estructurales + datos IC50

#### Estructura del CSV Exportado
```csv
Residue_ID,Residue_Name,Chain,Position,Degree_Centrality,Betweenness_Centrality,Closeness_Centrality,Eigenvector_Centrality,Clustering_Coefficient,Peptide,IC50_Value,IC50_Unit
μ-TRTX-Hd1a_1,MET,A,1,0.023,0.0045,0.1234,0.0891,0.456,μ-TRTX-Hd1a,150.0,nM
μ-TRTX-Hd1a_2,CYS,A,2,0.045,0.0123,0.1567,0.1234,0.567,μ-TRTX-Hd1a,150.0,nM
```

#### Aplicaciones Científicas
- **Análisis comparativo**: Comparar métricas entre diferentes familias
- **Identificación de patrones**: Encontrar residuos conservados críticos
- **Correlación SAR**: Relacionar propiedades estructurales con actividad biológica
- **Clasificación filogenética**: Agrupar toxinas por características topológicas

### Mejoras Técnicas Implementadas

#### Correcciones de Formato
- **Visualización de residuos**: Formato estandarizado "VAL21 (Cadena A): 0.1122"
- **Función `populateTop5List`**: Corrección completa para mostrar nombres de aminoácidos correctos
- **Manejo de valores undefined**: Eliminación de campos "undefined" en la interfaz

#### Optimizaciones de Rendimiento
- **Consultas SQL optimizadas**: Queries específicas por familia para mejor rendimiento
- **Normalización de IC50**: Algoritmo eficiente para conversión de unidades
- **Manejo de Unicode**: Mapeo de caracteres griegos para compatibilidad de archivos

#### Sistema de Logging
- **Debugging avanzado**: Logs detallados para el proceso de exportación de familias
- **Tracking de errores**: Identificación específica de problemas en consultas de base de datos
- **Monitoreo de rendimiento**: Seguimiento de tiempos de procesamiento

#### Resolución de Conflictos
- **Rutas duplicadas**: Eliminación del conflicto `/export_family_csv` en viewer_routes.py
- **Consolidación de funciones**: Unificación de lógica de exportación
- **Manejo de errores**: Sistema robusto de captura y manejo de excepciones

### Paso 6: Análisis por familias (Nuevo)
- **Seleccionar familia**: Usar el selector de familia para análisis comparativo
- **Exportar por familia**: Descargar datasets completos de familias específicas
- **Análisis IC50**: Revisar correlaciones estructura-actividad en los datos exportados
- **Comparación de subfamilias**: Evaluar diferencias entre μ-TRTX-H y μ-TRTX-C



## 🐛 Solución de Problemas

### Error: "No module named 'graphein'"
```powershell
pip install graphein
```

### Error: "SQLite database is locked"
```powershell
# Cerrar todas las conexiones a la base de datos
python -c "import sqlite3; conn = sqlite3.connect('database/toxins.db'); conn.close()"
```

### Error de permisos en Windows
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Interface no carga
- Verificar que Flask esté ejecutándose en puerto 5000
- Comprobar que no hay conflictos con otros servicios
- Revisar logs en la consola del navegador

### Problemas con Exportación de Familias

#### CSV vacío o no se descarga
```python
# Verificar datos en la base
import sqlite3
conn = sqlite3.connect('database/toxins.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM Nav1_7_InhibitorPeptides WHERE peptide_name LIKE 'μ-TRTX-%'")
print(f"Registros encontrados: {cursor.fetchone()[0]}")
```

#### Error en caracteres Unicode
- **Problema**: Nombres de archivo con caracteres griegos causan errores
- **Solución**: El sistema convierte automáticamente μ→mu, κ→kappa, etc.

#### Valores IC50 incorrectos
- **Verificar normalización**: Todos los valores deben estar en nM
- **Unidades soportadas**: nM, μM, mM (conversión automática)

### Problemas de Visualización

#### Residuos muestran "undefined"
- **Causa**: Error en función `populateTop5List` 
- **Estado**: ✅ **RESUELTO** en v1.2.0
- **Verificación**: Los residuos ahora muestran formato "VAL21 (Cadena A): 0.1122"

#### Métricas no calculan correctamente
```python
# Verificar parámetros de entrada
threshold = 8.0  # Distancia recomendada
granularity = "CA"  # Nivel de residuo
sequence_separation = 5  # Separación secuencial
```

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📚 Referencias Científicas

- **Graphein**: "Graphein: a Python library for geometric deep learning and network analysis on biomolecular structures"
- **Mol***: "Mol* Viewer: modern web app for 3D visualization and analysis of large biomolecular structures"
- **NetworkX**: "Exploring network structure, dynamics, and function using NetworkX"
- **Nav1.7**: "Voltage-gated sodium channel Nav1.7 and pain: from gene to pharmacology"
- **Pharmacophore**: En el paper de Sharma FEBS Letters - 2025 - S… es: X1X2-S-WCKX3 → patrón basado en los residuos críticos para inhibición de Nav1.7.
→ Deberías poner una frase corta cuando usas el campo "Pharmacophore" en la tabla:
Patrón de residuos críticos que definen la actividad inhibidora sobre Nav1.7 (ver Sharma et al., 2025).



## 👥 Autores

- **Desarrolladores Principal**: 


## 🆘 Soporte

Para preguntas técnicas o científicas:
- **Issues**: GitHub Issues del proyecto
- **Email**: [tu-email@ejemplo.com]
- **Documentación**: Wiki del proyecto

## 🔄 Actualizaciones Recientes

### v1.2.0 (Junio 2025) - **NUEVA VERSIÓN**
- ✅ **Exportación por Familias**: Sistema completo de exportación CSV agrupado por familias de toxinas
- ✅ **Integración IC50**: Correlación automática con datos de actividad biológica (nM)
- ✅ **Diferenciación de Subfamilias**: Clasificación μ-TRTX-H (2a) vs μ-TRTX-C (2b)


### v1.1.0 (Junio 2025)
- ✅ Corrección de formato de visualización de residuos
- ✅ Mejoras en la función `populateTop5List`
- ✅ Optimización de consultas de base de datos
- ✅ Resolución de conflictos de rutas duplicadas

### v1.0.0 (Junio 2025)
- ✅ Sistema completo de análisis de grafos moleculares
- ✅ Interface web con Mol* viewer integrado
- ✅ Exportación de métricas en CSV
- ✅ Base de datos SQLite optimizada
- ✅ Soporte para análisis de toxinas Nav1.7

---

