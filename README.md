# Proyecto Toxinas - Análisis de Toxinas Nav1.7

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Mol*](https://img.shields.io/badge/Mol*-Latest-orange.svg)](https://molstar.org/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Latest-red.svg)](https://networkx.org/)

Un proyecto de análisis computacional para estudiar Toxinas que interactúan con canales de sodio Nav1.7, utilizando análisis de grafos moleculares y visualización 3D interactiva con métricas de centralidad avanzadas.

## 🧬 Descripción

Este proyecto proporciona herramientas para analizar la estructura y propiedades de péptidos tóxicos que se dirigen específicamente a los canales de sodio Nav1.7. Combina análisis de grafos moleculares con visualización 3D interactiva para identificar residuos críticos y patrones estructurales.

### Características Principales

- **Análisis de Centralidad**: Cálculo de métricas de centralidad (betweenness, closeness, eigenvector, degree) para identificar residuos importantes
- **Visualización 3D**: Integración completa con Molstar para visualización molecular interactiva
- **Exportación de Datos**: Funcionalidad completa de exportación CSV con todas las métricas de residuos
- **Base de Datos**: Sistema de almacenamiento SQLite para gestión eficiente de estructuras PDB
- **Métricas en Tiempo Real**: Visualización dinámica de métricas con formato "VAL21 (Cadena A): 0.1122"

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
- **Eigenvector Centrality**: Identifica residuos conectados a otros residuos importantes

### Formato de Visualización

Las métricas se muestran en el formato optimizado: `"VAL21 (Cadena A): 0.1122"`

### Funcionalidad de Exportación CSV

El archivo CSV exportado incluye todas las métricas calculadas:
- ID del residuo
- Nombre del residuo  
- Cadena
- Posición
- Degree centrality
- Betweenness centrality
- Closeness centrality  
- Eigenvector centrality
- Clustering coefficient
matplotlib >= 3.5.0        # Visualización estática
seaborn >= 0.11.0          # Visualización estadística
plotly >= 5.0.0            # Visualización interactiva

# Framework web
flask >= 2.0.0             # Framework web principal
flask-cors >= 3.0.0        # Manejo de CORS

# Bases de datos y utilidades
sqlite3                    # Base de datos (incluido en Python)
requests >= 2.25.0         # Peticiones HTTP para APIs
aiohttp >= 3.8.0           # Peticiones asíncronas
lxml >= 4.6.0              # Procesamiento XML
```

## 🛠️ Instalación

### 1. Clonar el Repositorio
```bash
git clone https://github.com/usuario/proyecto-toxinas.git
cd proyecto-toxinas
```

### 2. Crear Entorno Virtual
```powershell
python -m venv venv

# Windows
venv\Scripts\Activate.ps1

# Si hay problemas de permisos, ejecutar:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar Dependencias
```powershell
pip install -r requirements.txt
```

### 4. Configurar Base de Datos
```powershell
# Crear la base de datos
python database/create_db.py

# Opcional: Insertar datos de ejemplo
python database/pdb_data_insert.py
```

### 5. Ejecutar la Aplicación
```powershell
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

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
Exporta métricas completas en formato CSV.

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

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📚 Referencias Científicas

- **Graphein**: "Graphein: a Python library for geometric deep learning and network analysis on biomolecular structures"
- **Mol***: "Mol* Viewer: modern web app for 3D visualization and analysis of large biomolecular structures"
- **NetworkX**: "Exploring network structure, dynamics, and function using NetworkX"
- **Nav1.7**: "Voltage-gated sodium channel Nav1.7 and pain: from gene to pharmacology"

## 👥 Autores

- **Desarrolladores Principal**: 


## 🆘 Soporte

Para preguntas técnicas o científicas:
- **Issues**: GitHub Issues del proyecto
- **Email**: [tu-email@ejemplo.com]
- **Documentación**: Wiki del proyecto

## 🔄 Actualizaciones Recientes

### v1.0.0 (Junio 2025)
- ✅ Sistema completo de análisis de grafos moleculares
- ✅ Interface web con Mol* viewer integrado
- ✅ Exportación de métricas en CSV
- ✅ Base de datos SQLite optimizada
- ✅ Soporte para análisis de toxinas Nav1.7

---

