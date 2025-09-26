# Carpeta `domain`

Esta capa contiene el modelo de dominio puro: **entidades**, **value objects** y **servicios de dominio** (lógica derivada que no depende de infraestructura). Todo aquí debe ser determinista y testeable sin IO externo.

## Objetivos
- Definir el vocabulario central (Toxin, Family, GraphMetrics, Dipole...).
- Encapsular invariantes y validaciones (p.ej. thresholds > 0, normalización IC50).
- Proveer estructuras semánticas sobre primitivas para que `application` pueda orquestar sin lógica ad-hoc.

## Estructura

```
domain/
  models/
    entities.py       # Entidades y agregados (Toxin, Family, Graph, GraphMetrics, etc.)
    value_objects.py  # Tipos de valor (Granularity, DistanceThreshold, IC50...)
  services/
    segmentation_service.py  # Lógica de agrupación/segmentación (residuos ↔ átomos)
```

## Value Objects (`models/value_objects.py`)
Los Value Objects (VO) encapsulan reglas y validaciones tempranas.

| VO | Propósito | Validaciones/Notas |
|----|-----------|-------------------|
| `Granularity` (Enum) | Escala del grafo (`CA` o `atom`) | `from_string` homogeniza entrada |
| `DistanceThreshold` | Umbral espacial (Å) | > 0 obligatorio, TypeError si no numérico |
| `SequenceSeparation` | Separación secuencial mínima para considerar arista | >= 0, entero |
| `ProteinId` | Identificador compuesto (fuente + id entero) | Inmutable; útil si se desea distinguir fuentes |
| `FamilyName` | Nombre/prefijo de familia | Normaliza letras griegas y genera patrones LIKE para consultas |
| `IC50` | Valor + unidad original | `to_nm()` y `normalize_to_nm` convierten a nM |
| `IC50Unit` (Enum) | Unidades soportadas (`nM`, `μM`, `mM`) | Mapeo insensible a mayúsculas; fallback para unidades desconocidas |

### Normalización IC50
`IC50.normalize_to_nm(valor, unidad)`:
- nM → valor
- μM → valor * 1e3
- mM → valor * 1e6
- Desconocido → devuelve número original (best effort)

## Entidades (`models/entities.py`)

| Entidad | Campos clave | Descripción |
|---------|--------------|-------------|
| `ProteinStructure` | id, nombre, sequence, pdb_data, psf_data | Representa la “carga” estructural asociada a una toxina |
| `GraphConfig` | granularity, distance_threshold, sequence_separation | Configuración semántica de un grafo proteico |
| `Graph` | nx_graph, config | Envoltura del grafo (NetworkX) + su configuración VO |
| `GraphTopResidue` | chain, residue_name, residue_number, value | Entrada de ranking de centralidades/top N |
| `GraphMetrics` | num_nodes, num_edges, density, avg_degree, avg_clustering, num_components, top5* | Métricas agregadas persistibles o exportables |
| `Toxin` | id, code, ic50, sequence, structure | Objeto de dominio de una toxina; `ic50` como VO opcional |
| `Family` | name, toxins (tuple) | Colección inmutable de toxinas relacionadas |
| `Dipole` | vector (x,y,z), magnitude, origin | Resultado abstraído del cálculo de momento dipolar |

Notas:
- `GraphMetrics` separa ranking por tipo de centralidad (top5) evitando recalcular en presentación.
- Entidades marcadas `frozen=True` son inmutables → hacen más seguras las referencias cruzadas.

## Servicio de Dominio: `segmentation_service.py`

### Función `agrupar_por_segmentos_atomicos(G, granularity="atom")`
Agrupa nodos (átomos) por residuo para generar una tabla (DataFrame) con métricas agregadas por “segmento” (residuo). Columnas resultantes:
| Columna | Significado |
|---------|-------------|
| `Segmento_ID` | Identificador formateado (ej. `RES_012`) |
| `Num_Atomos` | Número de átomos en el residuo |
| `Conexiones_Internas` | Aristas internas (o suma de grados si no hay subgrafos internos) |
| `Atomos_Lista` | Lista concatenada de nombres atómicos |
| `Residuo_Nombre`, `Residuo_Numero`, `Cadena` | Identificación estructural |
| `Grado_Promedio`, `Grado_Maximo`, `Grado_Minimo` | Estadísticos de grado sobre nodos atómicos |
| `Densidad_Segmento` | Densidad interna o aproximada (fallback) |
| `Centralidad_Grado_Promedio` | Media de centralidad (degree_centrality) del segmento |
| `Centralidad_Intermediacion_Promedio` | Media de betweenness centrality |
| `Centralidad_Cercania_Promedio` | Media de closeness |
| `Coeficiente_Agrupamiento_Promedio` | Media local de clustering |

Algoritmo:
1. Validar granularidad = `atom` (else DataFrame vacío).
2. Calcular centralidades globales (degree, betweenness, closeness, clustering) para reusar valores.
3. Agrupar nodos por (chain, residuo) extrayendo nombre/num desde atributos o parseando el identificador de nodo si es string con separadores.
4. Construir subgrafo por residuo: contar edges reales; fallback a suma de grados si subgrafo sin aristas (estructura lineal o aislada).
5. Calcular densidad interna (E / max_posibles) o aproximación basada en grados.
6. Agregar estadísticos y centralidades promedio por segmento.
7. Ordenar por cadena y número de residuo.

### Función `agrupar_por_segmentos(G, granularity="atom")`
Wrapper que delega a `agrupar_por_segmentos_atomicos` cuando granularidad es atómica; si no, genera un DataFrame simplificado (cada nodo/residuo como segmento unitario CA).

## Relación con Otras Capas

| Capa | Cómo usa `domain` |
|------|-------------------|
| application | Importa VO para validar entradas y empaquetar config; usa `segmentation_service` para exportes |
| infrastructure | Mapea filas SQLite → `Toxin`, `Family`; crea grafos y podría convertir a `GraphMetrics` (extensión futura) |
| interfaces | No debería instanciar entidades directamente (usa use cases) |


## Invariantes y Validación
- VO garantizan que no se cree un grafo con thresholds inválidos (se falla rápido).
- Conjunto de top5 en `GraphMetrics` siempre es tupla inmutable (evita mutaciones accidentales en presentación/export).
- `IC50` siempre se consulta a través de `to_nm()` para normalizar comparaciones.



## Riesgos / Consideraciones
- `GraphMetrics` aún no se instancia dentro de la infraestructura actual (se usan dicts); estandarizar podría reducir duplicación.
- Segmentación recalcula centralidades globales cada invocación; para grandes grafos se podría aceptar caches inyectados.
- `ProteinId` se define con `source` y `pid` pero algunos repos usan sólo `int`; mantener consistencia futura.
