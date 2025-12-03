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

Backend (ampliado):

- Flask 3.x / Werkzeug 3.x: servidor HTTP, middleware y routing por blueprints
- Jinja2: templates HTML con parciales reutilizables (navbar)
- Configuración: `src/config.py` / `.env` (dataclass `AppConfig` y flags: `USE_MINIFIED_ASSETS`, `LEGACY_ALIASES_ENABLED`, `DEBUG`)
- SQLite (`database/toxins.db`): metadatos, secuencias, IC50/Kd AI, y grafos cacheados en BLOB
- Repositorios SQLite: `SqliteStructureRepository`, `SqliteMetadataRepository`, `SqliteFamilyRepository`, `SqliteToxinRepository`
- Adaptadores: `GrapheinGraphAdapter`, `DipoleAdapter`, `ExcelExportAdapter`, `PDBPreprocessorAdapter`, `TempFileService`
- Graphein 1.7.x + NetworkX 2.6+: construcción de grafos y métricas (grado, intermediación, cercanía, eigenvector, clustering, densidad)
- MDAnalysis 2.7.0 / BioPython 1.79+: cálculo de momento dipolar (PSF/PDB), fallback por aproximación
- openpyxl 3.1.5: generación de informes Excel (por toxina, familia, segmentos atómicos)
- Bioservices + requests-cache: ingesta de UniProt con caching HTTP
- Parasail: alineamiento de secuencias para detección de motivos
- Loguru, Pydantic: logging estructurado y validación de datos en casos de uso
- ProxyFix (Werkzeug): despliegue tras Nginx Proxy Manager, confianza en `X-Forwarded-*`
- Flask-Compress: compresión gzip, `after_request`: cache/security headers

Frontend (ampliado):

- Mol* Plugin: visualizador 3D principal (estructura)
- py3Dmol: visualización de dipolos por tarjeta/peptido
- WebGL Canvas custom: `MolstarGraphRenderer` para grafos densos sub-segundo
- Plotly 5/6: gráficas interactivas (IC50 scatter, rose plots angulares)
- Design System CSS: `design-system.css`, `components.css`, `navbar.css`, CSS variables y tokens
- SheetJS (XLSX.js): exportación Excel en cliente (filtro toxinas)
- Arquitectura MPA: `viewer.html`, `toxin_filter.html`, `dipole_families.html` con assets específicos y parciales `partials/navbar.html`
- Carga diferida: `IntersectionObserver`, lazy import de Plotly/3Dmol/SheetJS, Web Worker para datasets
- Accesibilidad: atributos ARIA, navegación por teclado, contraste WCAG AA

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

---

## Diagramas (enlaces originales)

- Arquitectura general: <https://deepwiki.com/Juaker1/Proyecto-toxinas/3-architecture-overview>
	- Diagrama de capas, flujo de dependencias, composición en `create_app_v2()`
- Backend Architecture: <https://deepwiki.com/Juaker1/Proyecto-toxinas/3.1-backend-architecture>
	- Organización de blueprints `/v2`, patrón de inyección manual, flujos de petición/exportación
- Frontend Architecture: <https://deepwiki.com/Juaker1/Proyecto-toxinas/3.2-frontend-architecture>
	- Arquitectura de páginas (MPA), mapa de módulos JS, renderer WebGL, sistema de modales
- Database Schema: <https://deepwiki.com/Juaker1/Proyecto-toxinas/6.1-database-schema>
	- Diagrama ER, tablas núcleo, estrategia BLOB vs filesystem
- Installation & Dependencies: <https://deepwiki.com/Juaker1/Proyecto-toxinas/2.1-installation-and-dependencies>
	- Requisitos del sistema, categorías de dependencias, flujo de configuración, salud y troubleshooting

Nota: Los diagramas están embebidos en DeepWiki; aquí se enlazan para mantener fidelidad y evitar pérdida de detalle. Si prefieres una exportación de imágenes local, puedo descargarlas y referenciarlas en `docs/wiki_export/img/`.

---

## Pipeline de extracción y análisis (resumen)

Esta sección sintetiza el flujo de trabajo de la plataforma desde la extracción y normalización de datos hasta el análisis topológico, basada en tu contenido y la estructura del sistema.

### Extracción y normalización de datos biomoleculares

- Consulta UniProt (familia Knottin, venenos, revisado): `keyword:"Knottin" AND (cc_tissue_specificity:venom OR cc_scl_term:nematocyst) AND reviewed:true`.
- Recuperación inicial: 1348 proteínas.
- Limpieza/normalización:
	- Extracción de coordenadas del péptido maduro (excluye pro-péptidos y señales).
	- Validación de estructura 3D (PDB o AlphaFold).
	- Recorte digital automatizado para alinear la estructura al segmento maduro.
- Resultado: 1308 secuencias válidas (≈97%).
- Distribución:
	- 40 estructuras recortadas automáticamente.
	- 1268 estructuras preexistentes validadas.

Tabla resumen (valores):

| Etapa del Proceso                  | Cantidad |
|-----------------------------------|----------|
| Proteínas recuperadas (UniProt)   | 1348     |
| Péptidos maduros validados        | 1308     |
| Estructuras recortadas automáticamente | 40  |
| Estructuras preexistentes validadas    | 1268 |

### Filtrado basado en motivo farmacofórico

- Criterio Sharma et al. (2025), NaSpTx1: patrón mínimo S–X(3,6)–W.
- Selección:
	- 50 péptidos cumplen el patrón (3.8% del dataset depurado).
	- Exclusión de toxinas del conjunto de referencia → 44 candidatos nuevos.
- Núcleo de análisis: 44 péptidos con alta probabilidad de bioactividad.

### Modelado estructural y generación de grafos moleculares

- Para los 44 candidatos:
	- PDB normalizados y PSF generados/validados (cobertura 100%).
	- Representación por grafos a dos granularidades: atómica y residuos (Cα).
- Métricas promedio en grafos de residuos: ~300 nodos y ~600 aristas por estructura.

### Análisis topológico y propiedades estructurales

- Patrones de centralidad asociados a actividad inhibidora; preservación de hubs crítica para afinidad.
- Ejemplos:
	- μ-TRTX-Hh2a: LEU22 y TRP30 mantienen alta conectividad (>1000 contactos externos) en WT y mutantes activos.
	- ω-TRTX-Gr2a: mutación W29A reduce ≈40% contactos externos en posición 29, desarticulando la interacción local.
- Sugerencia basada en literatura (Amitai 2004; del Sol 2006; Brysbaert 2021): usar betweenness y grado para predecir estabilidad funcional del farmacóforo; hubs topológicos correlacionan con integridad estructural.

### Relación con la arquitectura del sistema

- Ingesta y limpieza: `extractors/uniprot.py`, `extractors/peptide_extractor.py`, caching y normalización.
- Recorte/normalización PDB: `extractors/cortar_pdb.py`, `PDBPreprocessorAdapter`.
- PSF: `resources/psf_gen.tcl`, `psfs/` y pipelines VMD/psfgen (opcional en despliegue). 
- Grafos y métricas: `GrapheinGraphAdapter`, `domain/services/graph_metrics.py`, `SegmentationService`.
- Exportación: `ExcelExportAdapter` y casos de uso de export.
- Persistencia y BLOBs: `database/create_db.py`, almacenamiento dual (filesystem + SQLite BLOB).
