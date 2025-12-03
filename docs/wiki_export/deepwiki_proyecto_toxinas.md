# Proyecto Toxinas – DeepWiki (Resumen en Markdown)

Fuente: <https://deepwiki.com/Juaker1/Proyecto-toxinas>
Última indexación: 3 de diciembre de 2025 (commit `ba837e07`)

---

## Overview

Plataforma de investigación para toxinas dirigidas a Nav1.7 que combina procesamiento en lote offline con una aplicación web interactiva para:

- Visualización 3D (Mol*, py3Dmol)
- Construcción y análisis de grafos moleculares
- Cálculo de momentos dipolares
- Filtrado por motivos (fármacofores)
- Exportación de datos (XLSX/CSV)

### System Purpose

Objetivos principales:

1. Agregación automática de datos desde UniProt, PDB y AlphaFold
2. Enriquecimiento de datos farmacológicos con extracción de IC50/Kd vía few-shot
3. Visualización 3D interactiva con Mol* y py3Dmol
4. Análisis de grafos con métricas de centralidad y segmentación estructural
5. Cálculo de dipolo para análisis de orientación y comparación entre familias
6. Filtro por motivo para identificar toxinas que cumplan el patrón farmacóforo S-X(3,6)-W

Referencias: README y `src/interfaces/http/flask/app.py`.

### Architecture Overview

Separación clara entre:

- Pipeline offline (ingesta, PSF, análisis AI, persistencia en SQLite/sistema de archivos)
- Servicio online (Flask) con inyección de dependencias (`create_app_v2()`), capas: Controladores (HTTP), Casos de Uso (lógica), Infraestructura (interfaces externas)

### Core Technology Stack

Backend:

- Flask 2.0+: servidor HTTP y blueprints
- Configuración: `src/config.py` / `.env` (dataclass `AppConfig`)
- SQLite (`toxins.db`): metadatos, secuencias, IC50, grafos en BLOB
- Graphein 1.7.0+: construcción de grafos desde PDB
- NetworkX 2.6+: métricas de centralidad (betweenness, closeness, degree)
- MDAnalysis / BioPython: cálculo de dipolo desde PSF/PDB
- BioPython 1.79+: manipulación PDB y extracción de secuencia
- openpyxl: generación de Excel para reportes por residuo
- Werkzeug ProxyFix: manejo de `X-Forwarded-*` detrás de Nginx
- Flask-Compress: compresión gzip

Frontend:

- Mol* Plugin: visualizador 3D principal
- py3Dmol: visualización de vector de dipolo
- Canvas WebGL custom: `MolstarGraphRenderer` para grafos moleculares interactivos
- Plotly 5.0+: gráficas de IC50 y rose plots de ángulos
- Design System CSS: variables y temas
- SheetJS (XLSX.js): exportación Excel en cliente

### Application Composition Root

`create_app_v2()` actúa como composition root: instancia dependencias y las inyecta en módulos controladores mediante funciones `configure_*_dependencies()`. Inyección manual para mantener testabilidad y evitar “magia” de frameworks.

### Data Flow: User Request to Response

- UI → Controladores Flask (REST)
- Controladores → Casos de Uso (orquestación)
- Casos de Uso → Servicios de infraestructura (Graphein, MDAnalysis, SQLite)
- Repositorios → abstracción de acceso a datos

### Database Schema Overview

Entidades principales de `toxins.db`:

- Proteins: `accession_number` (PK), nombre, descripción, secuencia
- Peptides: `peptide_id` (PK), `peptide_name`, `pdb_file` (BLOB), secuencia
- Nav1_7_InhibitorPeptides: `peptide_code` (PK), `ic50_value`, `pdb_blob`, `psf_blob`, `graph_*` BLOBs
- ProteinShortNames / ProteinAlternativeNames: alias vinculados a `Proteins.accession_number`

Estrategia de almacenamiento:

- PDB/PSF como BLOB en `Nav1_7_InhibitorPeptides` para servir vía API, y en disco (`pdbs/`, `psfs/`) para pipeline
- Grafos precomputados serializados en BLOB para evitar reconstrucción costosa

### Key Configuration

- Carga desde variables de entorno con valores por defecto
- Referencia WT: `hwt4_Hh2a_WT` para comparación de dipolos (3 puentes disulfuro; 552 átomos, 35 residuos; generado con VMD/psfgen y CHARMM36)

### Deployment Architecture

- Producción en Docker con Gunicorn, expuesto en puerto host 8087
- Nginx Proxy Manager termina SSL y reenvía `X-Forwarded-*`
- `ProxyFix` reconstruye información original del cliente para URLs y logs correctos

### Primary Use Cases

1. Exploración de estructura: cargar PDB en Mol* y analizar controles 3D
2. Análisis de grafos: granularidad CA o atómica; calcular centralidades
3. Cálculo de dipolo: PSF/PDB, comparar orientaciones entre familias
4. Filtro por motivo: patrón farmacóforo S-X(3,6)-W con ajustes de gap
5. Comparación de familias: μ-TRTX-H, μ-TRTX-C, κ-TRTX con visualizaciones lado a lado
6. Exportación de datos: informes Excel con métricas por residuo y correlaciones IC50

### Health Monitoring

- `/v2/health`: estado de blueprints, rutas estáticas y configuración
- `/v2/db_check`: conectividad SQLite y conteo de filas

Usado en health checks Docker y monitoreo externo.

---

## Índice de páginas en DeepWiki

- Overview: <https://deepwiki.com/Juaker1/Proyecto-toxinas/1-overview>
- Getting Started: <https://deepwiki.com/Juaker1/Proyecto-toxinas/2-getting-started>
- Installation & Dependencies: <https://deepwiki.com/Juaker1/Proyecto-toxinas/2.1-installation-and-dependencies>
- Configuration: <https://deepwiki.com/Juaker1/Proyecto-toxinas/2.2-configuration>
- Architecture Overview: <https://deepwiki.com/Juaker1/Proyecto-toxinas/3-architecture-overview>
- Backend Architecture: <https://deepwiki.com/Juaker1/Proyecto-toxinas/3.1-backend-architecture>
- Frontend Architecture: <https://deepwiki.com/Juaker1/Proyecto-toxinas/3.2-frontend-architecture>
- Data Layer: <https://deepwiki.com/Juaker1/Proyecto-toxinas/3.3-data-layer>
- User Interfaces: <https://deepwiki.com/Juaker1/Proyecto-toxinas/4-user-interfaces>
- Protein Viewer Interface: <https://deepwiki.com/Juaker1/Proyecto-toxinas/4.1-protein-viewer-interface>
- 3D Structure Visualization: <https://deepwiki.com/Juaker1/Proyecto-toxinas/4.1.1-3d-structure-visualization>
- Graph Visualization System: <https://deepwiki.com/Juaker1/Proyecto-toxinas/4.1.2-graph-visualization-system>
- Export System: <https://deepwiki.com/Juaker1/Proyecto-toxinas/4.1.3-export-system>
- Toxin Filter Interface: <https://deepwiki.com/Juaker1/Proyecto-toxinas/4.2-toxin-filter-interface>
- Motif Dipoles Visualization: <https://deepwiki.com/Juaker1/Proyecto-toxinas/4.2.1-motif-dipoles-visualization>
- Dipole Families Analysis: <https://deepwiki.com/Juaker1/Proyecto-toxinas/4.3-dipole-families-analysis>
- Core Functionality: <https://deepwiki.com/Juaker1/Proyecto-toxinas/5-core-functionality>
- Protein Graph Construction: <https://deepwiki.com/Juaker1/Proyecto-toxinas/5.1-protein-graph-construction>
- Graph Metrics & Centrality: <https://deepwiki.com/Juaker1/Proyecto-toxinas/5.2-graph-metrics-and-centrality>
- Dipole Moment Calculation: <https://deepwiki.com/Juaker1/Proyecto-toxinas/5.3-dipole-moment-calculation>
- Structural Analysis: <https://deepwiki.com/Juaker1/Proyecto-toxinas/5.4-structural-analysis>
- Data Segmentation & Export: <https://deepwiki.com/Juaker1/Proyecto-toxinas/5.5-data-segmentation-and-export>
- Data Pipeline: <https://deepwiki.com/Juaker1/Proyecto-toxinas/6-data-pipeline>
- Database Schema: <https://deepwiki.com/Juaker1/Proyecto-toxinas/6.1-database-schema>
- Data Ingestion Pipeline: <https://deepwiki.com/Juaker1/Proyecto-toxinas/6.2-data-ingestion-pipeline>
- AI-Based IC50 Extraction: <https://deepwiki.com/Juaker1/Proyecto-toxinas/6.3-ai-based-ic50-extraction>
- API Reference: <https://deepwiki.com/Juaker1/Proyecto-toxinas/7-api-reference>
- Graph & Visualization Endpoints: <https://deepwiki.com/Juaker1/Proyecto-toxinas/7.1-graph-and-visualization-endpoints>
- Export Endpoints: <https://deepwiki.com/Juaker1/Proyecto-toxinas/7.2-export-endpoints>
- Toxin Filter & Family Endpoints: <https://deepwiki.com/Juaker1/Proyecto-toxinas/7.3-toxin-filter-and-family-endpoints>
- Deployment: <https://deepwiki.com/Juaker1/Proyecto-toxinas/8-deployment>
- Docker Deployment: <https://deepwiki.com/Juaker1/Proyecto-toxinas/8.1-docker-deployment>
- Production Setup: <https://deepwiki.com/Juaker1/Proyecto-toxinas/8.2-production-setup>
- Frontend Development: <https://deepwiki.com/Juaker1/Proyecto-toxinas/9-frontend-development>
- Design System: <https://deepwiki.com/Juaker1/Proyecto-toxinas/9.1-design-system>
- JavaScript Modules: <https://deepwiki.com/Juaker1/Proyecto-toxinas/9.2-javascript-modules>
- Testing & Debugging: <https://deepwiki.com/Juaker1/Proyecto-toxinas/9.3-testing-and-debugging>
- Appendix: <https://deepwiki.com/Juaker1/Proyecto-toxinas/10-appendix>
- Terminology & Concepts: <https://deepwiki.com/Juaker1/Proyecto-toxinas/10.1-terminology-and-concepts>
- File Formats: <https://deepwiki.com/Juaker1/Proyecto-toxinas/10.2-file-formats>

---

Notas:

- Este Markdown resume y normaliza el contenido del DeepWiki en español, preservando estructura y enlaces originales.
- Las tablas del stack se describen en texto por compatibilidad `.md`.
- Si deseas exportar cada página a `.md` individual, puedo generarlas dentro de `docs/wiki_export/` con nombres basados en el slug del DeepWiki.
