import networkx as nx
import pandas as pd
from functools import partial
from graphein.protein.config import ProteinGraphConfig
from graphein.protein.graphs import construct_graph
from graphein.protein.edges.distance import add_distance_threshold


def agrupar_por_segmentos_atomicos(G, granularity="atom"):
    """
    Agrupa átomos en segmentos basados en residuos del archivo PDB.
    Cada segmento representa un residuo individual con todos sus átomos.
    
    Args:
        G: Grafo de NetworkX (debe ser a nivel atómico)
        granularity: Granularidad del grafo ("atom" para segmentación)
        
    Returns:
        DataFrame con los datos de segmentos atómicos por residuo
    """
    if granularity != "atom":
        print("⚠️  La segmentación atómica requiere granularidad 'atom'")
        return pd.DataFrame()
    
    print(f"🔬 Iniciando segmentación atómica por residuos para grafo con {G.number_of_nodes()} nodos")
    
    # Agrupar átomos por residuo usando atributos del nodo
    residuos_atomicos = {}
    
    for nodo, data in G.nodes(data=True):
        # Extraer información del residuo desde los atributos del nodo
        cadena = data.get('chain_id', 'A')
        residuo_nombre = data.get('residue_name', 'UNK')
        residuo_numero = data.get('residue_number', 1)
        atomo_nombre = data.get('atom_name', 'UNK')
        
        # Clave del residuo basada en cadena y número de residuo
        residuo_key = f"{cadena}_{residuo_numero}"
        
        if residuo_key not in residuos_atomicos:
            residuos_atomicos[residuo_key] = {
                'cadena': cadena,
                'residuo_nombre': residuo_nombre,
                'residuo_numero': residuo_numero,
                'atomos': []
            }
        
        residuos_atomicos[residuo_key]['atomos'].append({
            'nodo': nodo,
            'atomo_nombre': atomo_nombre
        })
    
    print(f"📊 Encontrados {len(residuos_atomicos)} residuos con átomos")
    
    segmentos_data = []
    
    for idx, (residuo_key, residuo_info) in enumerate(residuos_atomicos.items()):
        segmento_id = f"RES_{residuo_info['residuo_numero']:03d}"
        
        # Lista de nodos de átomos para este residuo
        atomos_nodos = [atomo['nodo'] for atomo in residuo_info['atomos']]
        atomos_nombres = [atomo['atomo_nombre'] for atomo in residuo_info['atomos']]
        
        # Crear subgrafo para análisis de métricas
        subgrafo = G.subgraph(atomos_nodos)
        
        # Calcular métricas del residuo
        num_atomos = len(atomos_nodos)
        num_conexiones = subgrafo.number_of_edges()
        
        # Grado promedio del residuo
        if num_atomos > 0:
            grados = [subgrafo.degree(nodo) for nodo in atomos_nodos]
            grado_promedio = sum(grados) / len(grados)
            grado_max = max(grados)
            grado_min = min(grados)
        else:
            grado_promedio = grado_max = grado_min = 0
        
        # Centralidades del residuo
        if num_atomos > 1:
            try:
                degree_centrality = nx.degree_centrality(subgrafo)
                betweenness_centrality = nx.betweenness_centrality(subgrafo)
                closeness_centrality = nx.closeness_centrality(subgrafo)
                clustering_coeff = nx.clustering(subgrafo)
                
                degree_cent_avg = sum(degree_centrality.values()) / len(degree_centrality)
                between_cent_avg = sum(betweenness_centrality.values()) / len(betweenness_centrality)
                close_cent_avg = sum(closeness_centrality.values()) / len(closeness_centrality)
                cluster_avg = sum(clustering_coeff.values()) / len(clustering_coeff)
                
            except Exception:
                degree_cent_avg = between_cent_avg = close_cent_avg = cluster_avg = 0
        else:
            degree_cent_avg = between_cent_avg = close_cent_avg = cluster_avg = 0
        
        # Densidad del residuo
        densidad_segmento = nx.density(subgrafo) if num_atomos > 1 else 0
        
        # Crear entrada del DataFrame
        segmento_info = {
            'Segmento_ID': segmento_id,
            'Num_Atomos': num_atomos,
            'Num_Conexiones': num_conexiones,
            'Atomos_Lista': ', '.join(sorted(atomos_nombres)),
            'Residuo_Nombre': residuo_info['residuo_nombre'],
            'Residuo_Numero': residuo_info['residuo_numero'],
            'Cadena': residuo_info['cadena'],
            'Grado_Promedio': round(grado_promedio, 6),
            'Grado_Maximo': grado_max,
            'Grado_Minimo': grado_min,
            'Densidad_Segmento': round(densidad_segmento, 6),
            'Centralidad_Grado_Promedio': round(degree_cent_avg, 6),
            'Centralidad_Intermediacion_Promedio': round(between_cent_avg, 6),
            'Centralidad_Cercania_Promedio': round(close_cent_avg, 6),
            'Coeficiente_Agrupamiento_Promedio': round(cluster_avg, 6)
        }
        
        segmentos_data.append(segmento_info)
    
    # Ordenar por número de residuo
    segmentos_data.sort(key=lambda x: (x['Cadena'], x['Residuo_Numero']))
    
    print(f"🎯 Segmentación completada: {len(segmentos_data)} residuos procesados")
    
    return pd.DataFrame(segmentos_data)


def agrupar_por_segmentos(G, granularity="atom"):
    """
    Función principal de segmentación que decide el método según la granularidad
    """
    if granularity == "atom":
        return agrupar_por_segmentos_atomicos(G, granularity)
    
    # Para granularidad CA, devolver análisis por residuo individual
    segmentos = []
    for node, data in G.nodes(data=True):
        chain = data.get('chain_id', 'A')
        residue_name = data.get('residue_name', 'UNK')
        residue_number = data.get('residue_number', 1)
            
        segmentos.append({
            'Segmento_ID': f"{chain}:{residue_name}:{residue_number}",
            'Cadena': chain,
            'Residuo_Nombre': residue_name,
            'Residuo_Numero': residue_number,
            'Atomos_Lista': f"{residue_name}{residue_number}:CA",
            'Num_Atomos': 1,
            'Grado_Nodo': G.degree(node)
        })
    
    return pd.DataFrame(segmentos)


def validar_segmentacion(df_segmentos):
    """
    Valida que la segmentación sea correcta
    """
    if df_segmentos.empty:
        print("⚠️ DataFrame de segmentos está vacío")
        return False
    
    total_atomos = df_segmentos['Num_Atomos'].sum()
    num_segmentos = len(df_segmentos)
    
    print(f"📋 Validación de segmentación:")
    print(f"   - Total de segmentos: {num_segmentos}")
    print(f"   - Total de átomos procesados: {total_atomos}")
    print(f"   - Segmento más grande: {df_segmentos['Num_Atomos'].max()} átomos")
    print(f"   - Segmento más pequeño: {df_segmentos['Num_Atomos'].min()} átomos")
    print(f"   - Promedio de átomos por segmento: {df_segmentos['Num_Atomos'].mean():.2f}")
    
    return True

def generate_segment_groupings(pdb_path, source, protein_id, long_range, threshold, granularity, toxin_name):
    cfg = ProteinGraphConfig(
        granularity=granularity,
        edge_construction_functions=[
            partial(add_distance_threshold,
                    long_interaction_threshold=long_range,
                    threshold=threshold)
        ]
    )
    G = construct_graph(config=cfg, path=pdb_path)
    G = G.to_undirected()
    return agrupar_por_segmentos(G, granularity=granularity)
