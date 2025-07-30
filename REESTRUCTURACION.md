# Reestructuración del Proyecto de Toxinas

## 📋 Resumen de la Reestructuración

Se ha reestructurado completamente el archivo `viewer_routes.py` (~1500 líneas) en múltiples módulos organizados por responsabilidad, manteniendo **toda la funcionalidad original** intacta.

## 🏗️ Nueva Estructura

### 📁 Servicios (`app/services/`)

#### 1. `database_service.py`
**Responsabilidad**: Todas las operaciones de base de datos SQLite
- ✅ Conexiones centralizadas a la base de datos
- ✅ Consultas para toxinas y Nav1.7
- ✅ Obtención de datos PDB y PSF
- ✅ Información de IC50 y metadatos

#### 2. `pdb_processor.py`
**Responsabilidad**: Procesamiento de archivos PDB y PSF
- ✅ Preprocesamiento de PDB para Graphein
- ✅ Conversión de residuos no estándar
- ✅ Manejo de archivos temporales
- ✅ Utilidades para nombres de archivos

#### 3. `graph_analyzer.py`
**Responsabilidad**: Análisis de grafos de proteínas
- ✅ Construcción de grafos con Graphein
- ✅ Cálculo de métricas de centralidad
- ✅ Propiedades del grafo (densidad, clustering, etc.)
- ✅ Estadísticas y análisis completo

#### 4. `graph_visualizer.py`
**Responsabilidad**: Visualización de grafos con Plotly
- ✅ Creación de visualizaciones interactivas
- ✅ Configuración de layouts y estilos
- ✅ Conversión de arrays NumPy para JSON

#### 5. `export_service.py`
**Responsabilidad**: Exportación de datos a Excel/CSV
- ✅ Preparación de datos para exportación
- ✅ Generación de metadatos
- ✅ Creación de archivos Excel por toxina/familia
- ✅ Comparaciones entre toxinas

#### 6. `dipole_service.py`
**Responsabilidad**: Análisis de momento dipolar
- ✅ Cálculos con archivos PDB/PSF
- ✅ Integración con `Nav17ToxinGraphAnalyzer`
- ✅ Validación de datos de entrada

#### 7. `comparison_service.py`
**Responsabilidad**: Comparaciones entre toxinas WT y referencia
- ✅ Procesamiento de toxinas individuales
- ✅ Mapeo de familias WT
- ✅ Análisis comparativo

### 📁 Rutas (`app/routes/`)

#### 1. `basic_routes.py`
**Endpoints básicos**:
- `GET /` - Página principal
- `GET /get_pdb/<source>/<pid>` - Obtener datos PDB
- `GET /get_psf/<source>/<pid>` - Obtener datos PSF
- `GET /get_toxin_name/<source>/<pid>` - Obtener nombre de toxina

#### 2. `graph_routes.py`
**Análisis de grafos**:
- `GET /get_protein_graph/<source>/<pid>` - Análisis completo de grafo

#### 3. `export_routes.py`
**Exportación de datos**:
- `GET /export_residues_xlsx/<source>/<pid>` - Exportar residuos
- `GET /export_segments_atomicos_xlsx/<source>/<pid>` - Segmentación atómica
- `GET /export_family_xlsx/<family_prefix>` - Familias completas

#### 4. `dipole_routes.py`
**Análisis dipolar**:
- `POST /calculate_dipole` - Desde archivos subidos
- `POST /calculate_dipole_from_db/<source>/<pid>` - Desde base de datos

#### 5. `comparison_routes.py`
**Comparaciones WT**:
- `GET /export_wt_comparison_xlsx/<wt_family>` - Comparación WT vs referencia

#### 6. `misc_routes.py`
**Funcionalidades adicionales**:
- `GET /export_segment_nodes/<source>/<pid>` - Segmentación de nodos

## 🔧 Archivos Mantenidos

### `app/utils/`
- ✅ `excel_export.py` - Mantenido sin cambios
- ✅ `graph_segmentation.py` - Mantenido sin cambios

### Otros archivos
- ✅ `app/__init__.py` - Actualizado para registrar todos los blueprints
- ✅ `viewer_routes.py` - **ARCHIVO ORIGINAL PRESERVADO** (no modificado)

## 🚀 Beneficios de la Reestructuración

### 1. **Separación de Responsabilidades**
- Cada módulo tiene una responsabilidad clara
- Fácil mantenimiento y debugging
- Código más legible y organizado

### 2. **Modularidad**
- Servicios reutilizables
- Facilita testing unitario
- Extensibilidad mejorada

### 3. **Escalabilidad**
- Fácil agregar nuevas funcionalidades
- Mejor organización para proyectos grandes
- Arquitectura más profesional

### 4. **Mantenibilidad**
- Errores más fáciles de localizar
- Modificaciones aisladas por módulo
- Documentación clara por responsabilidad

## 📋 Funcionalidades Preservadas

✅ **Todas las rutas originales funcionan igual**
✅ **Misma API y parámetros**
✅ **Misma lógica de negocio**
✅ **Mismos formatos de exportación**
✅ **Compatibilidad total con el frontend**

### Rutas principales mantenidas:
1. Visualización de proteínas (PDB/PSF)
2. Análisis de grafos moleculares
3. Exportación individual y por familias
4. Análisis de momento dipolar
5. Comparaciones WT vs referencia
6. Segmentación atómica y por residuos

## 🎯 Cómo Usar la Nueva Estructura

### Para desarrollar nuevas funcionalidades:
1. **Agregar lógica de base de datos** → `database_service.py`
2. **Procesar archivos** → `pdb_processor.py`
3. **Análisis de grafos** → `graph_analyzer.py`
4. **Nuevas visualizaciones** → `graph_visualizer.py`
5. **Exportaciones** → `export_service.py`
6. **Nuevas rutas** → Crear nuevo archivo en `routes/`

### Para modificar funcionalidades existentes:
1. Localizar el servicio responsable
2. Modificar solo ese módulo
3. Los cambios se propagan automáticamente

## 🔄 Migración

**El archivo original `viewer_routes.py` se mantiene intacto** para referencia y rollback si es necesario. La nueva estructura está completamente funcional y lista para usar.

### Para activar la nueva estructura:
1. Los nuevos blueprints ya están registrados en `app/__init__.py`
2. Todas las rutas están disponibles inmediatamente
3. No se requieren cambios en el frontend

### Para volver al sistema anterior:
1. Comentar los nuevos blueprints en `app/__init__.py`
2. Descomentar el blueprint original
3. Sistema vuelve al estado anterior instantáneamente

## 📈 Métricas de Mejora

- **Líneas por archivo**: Reducido de ~1500 a ~100-300 líneas promedio
- **Cohesión**: Cada módulo tiene una responsabilidad específica
- **Acoplamiento**: Reducido mediante interfaces claras
- **Mantenibilidad**: Incrementada significativamente
- **Testabilidad**: Cada servicio puede ser testeado independientemente

Esta reestructuración convierte el proyecto en una aplicación más profesional, mantenible y escalable, sin perder ninguna funcionalidad existente.
