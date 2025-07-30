"""
Servicio para análisis de grafos de proteínas.
Este módulo maneja la construcción de grafos, cálculo de métricas y análisis de centralidad.
"""

import networkx as nx
import numpy as np
from functools import partial
from graphein.protein.config import ProteinGraphConfig
from graphein.protein.graphs import construct_graph
from graphein.protein.edges.distance import add_distance_threshold
from graphein.protein.features.nodes.amino_acid import amino_acid_one_hot
from graphein.protein.features.nodes.geometry import add_sidechain_vector
from typing import Dict, Any, List, Tuple


class GraphAnalyzer:
    """Clase para análisis de grafos de proteínas."""
    
    @staticmethod
    def create_graph_config(granularity: str, long_threshold: int, distance_threshold: float) -> ProteinGraphConfig:
        """
        Crea la configuración para construir un grafo de proteína.
        
        Args:
            granularity: Granularidad del grafo ('atom' o 'CA')
            long_threshold: Umbral para interacciones de largo alcance
            distance_threshold: Umbral de distancia para conexiones
            
        Returns:
            Configuración del grafo
        """
        edge_functions = [
            partial(add_distance_threshold,
                    long_interaction_threshold=long_threshold,
                    threshold=distance_threshold)
        ]
        
        if granularity == 'atom':
            return ProteinGraphConfig(
                granularity="atom",
                edge_construction_functions=edge_functions
            )
        else:
            return ProteinGraphConfig(
                granularity="CA",
                edge_construction_functions=edge_functions
            )
    
    @staticmethod
    def construct_protein_graph(pdb_path: str, config: ProteinGraphConfig):
        """
        Construye un grafo de proteína desde un archivo PDB.
        
        Args:
            pdb_path: Ruta del archivo PDB
            config: Configuración del grafo
            
        Returns:
            Grafo de NetworkX
        """
        return construct_graph(config=config, pdb_code=None, path=pdb_path)
    
    @staticmethod
    def compute_graph_properties(G) -> Dict[str, Any]:
        """
        Calcula propiedades básicas del grafo.
        
        Args:
            G: Grafo de NetworkX
            
        Returns:
            Diccionario con propiedades del grafo
        """
        props = {}
        props["num_nodes"] = G.number_of_nodes()
        props["num_edges"] = G.number_of_edges()
        props["density"] = nx.density(G)
        
        degrees = list(dict(G.degree()).values())
        props["avg_degree"] = sum(degrees) / len(degrees) if degrees else 0.0
        
        props["avg_clustering"] = nx.average_clustering(G)
        
        # Componentes conectados
        if G.is_directed():
            comps = list(nx.weakly_connected_components(G))
        else:
            comps = list(nx.connected_components(G))
        props["num_components"] = len(comps)
        
        return props
    
    @staticmethod
    def compute_centrality_metrics(G) -> Dict[str, Dict]:
        """
        Calcula métricas de centralidad para todos los nodos del grafo.
        
        Args:
            G: Grafo de NetworkX
            
        Returns:
            Diccionario con métricas de centralidad
        """
        return {
            "degree": nx.degree_centrality(G),
            "betweenness": nx.betweenness_centrality(G),
            "closeness": nx.closeness_centrality(G),
            "clustering": nx.clustering(G)
        }
    
    @staticmethod
    def compute_centrality_statistics(centrality_metrics: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Calcula estadísticas de las métricas de centralidad.
        
        Args:
            centrality_metrics: Métricas de centralidad por nodo
            
        Returns:
            Estadísticas de centralidad
        """
        stats = {}
        
        for metric_name, metric_values in centrality_metrics.items():
            values = list(metric_values.values())
            if values:
                stats[f"{metric_name}_min"] = min(values)
                stats[f"{metric_name}_max"] = max(values)
                stats[f"{metric_name}_mean"] = sum(values) / len(values)
                
                # Encontrar residuos con valor máximo
                max_value = max(values)
                top_residues = [node for node, value in metric_values.items() 
                               if abs(value - max_value) < 0.0001]
                stats[f"{metric_name}_top"] = {
                    "residues": top_residues,
                    "value": max_value
                }
                
                # Top 5 residuos para cada métrica
                top5 = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)[:5]
                formatted_top5 = []
                for node_id, value in top5:
                    # Procesar el node_id que viene como "A:LYS:14:CE"
                    parts = str(node_id).split(':')
                    if len(parts) >= 3:
                        formatted_top5.append({
                            "residue": parts[2],
                            "value": value,
                            "residueName": parts[1],
                            "chain": parts[0]
                        })
                    else:
                        formatted_top5.append({
                            "residue": str(node_id),
                            "value": value,
                            "residueName": "UNK",
                            "chain": "A"
                        })
                
                stats[f"{metric_name}_top5"] = formatted_top5
        
        return stats
    
    @staticmethod
    def compute_complete_graph_analysis(G) -> Dict[str, Any]:
        """
        Realiza un análisis completo del grafo incluyendo propiedades y centralidades.
        
        Args:
            G: Grafo de NetworkX
            
        Returns:
            Análisis completo del grafo
        """
        # Propiedades básicas
        props = GraphAnalyzer.compute_graph_properties(G)
        
        # Métricas de centralidad
        centrality_metrics = GraphAnalyzer.compute_centrality_metrics(G)
        
        # Estadísticas de centralidad
        centrality_stats = GraphAnalyzer.compute_centrality_statistics(centrality_metrics)
        
        # Combinar todo
        props.update(centrality_stats)
        props["centrality"] = centrality_metrics
        
        return props
    
    @staticmethod
    def create_summary_statistics(props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea estadísticas resumidas para el frontend.
        
        Args:
            props: Propiedades del grafo
            
        Returns:
            Estadísticas resumidas
        """
        def format_top_residues(metric_name: str) -> str:
            top_data = props.get(f'{metric_name}_top', {})
            residues = top_data.get('residues', [])
            value = top_data.get('value', 0)
            return f"{', '.join(map(str, residues))} (valor: {value:.4f})"
        
        return {
            "degree_centrality": {
                "min": props.get("degree_min", 0),
                "max": props.get("degree_max", 0),
                "mean": props.get("degree_mean", 0),
                "top_residues": format_top_residues("degree")
            },
            "betweenness_centrality": {
                "min": props.get("betweenness_min", 0),
                "max": props.get("betweenness_max", 0),
                "mean": props.get("betweenness_mean", 0),
                "top_residues": format_top_residues("betweenness")
            },
            "closeness_centrality": {
                "min": props.get("closeness_min", 0),
                "max": props.get("closeness_max", 0),
                "mean": props.get("closeness_mean", 0),
                "top_residues": format_top_residues("closeness")
            },
            "clustering_coefficient": {
                "min": props.get("clustering_min", 0),
                "max": props.get("clustering_max", 0),
                "mean": props.get("clustering_mean", 0),
                "top_residues": format_top_residues("clustering")
            }
        }
    
    @staticmethod
    def extract_top5_residues(props: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Extrae los top 5 residuos para cada métrica de centralidad.
        
        Args:
            props: Propiedades del grafo
            
        Returns:
            Top 5 residuos por métrica
        """
        return {
            "degree_centrality": props.get("degree_top5", []),
            "betweenness_centrality": props.get("betweenness_top5", []),
            "closeness_centrality": props.get("closeness_top5", []),
            "clustering_coefficient": props.get("clustering_top5", [])
        }


class ResidueAnalyzer:
    """Clase para análisis específico de residuos."""
    
    @staticmethod
    def extract_residue_data(G, granularity: str) -> List[Dict[str, Any]]:
        """
        Extrae datos de residuos del grafo para exportación.
        
        Args:
            G: Grafo de NetworkX
            granularity: Granularidad del grafo
            
        Returns:
            Lista de datos de residuos
        """
        # Calcular métricas de centralidad
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        clustering_coefficient = nx.clustering(G)
        
        residue_data = []
        for node in G.nodes():
            if granularity == 'CA':
                # Para granularidad CA, parsear el ID del nodo
                parts = str(node).split(':')
                if len(parts) >= 3:
                    chain = parts[0]
                    residue_name = parts[1]
                    residue_number = parts[2]
                else:
                    chain = G.nodes[node].get('chain_id', 'A')
                    residue_name = G.nodes[node].get('residue_name', 'UNK')
                    residue_number = str(node)
            else:  # granularidad atómica
                chain = G.nodes[node].get('chain_id', 'A')
                residue_name = G.nodes[node].get('residue_name', 'UNK')
                residue_number = str(G.nodes[node].get('residue_number', node))
            
            residue_data.append({
                'Cadena': chain,
                'Residuo_Nombre': residue_name,
                'Residuo_Numero': residue_number,
                'Centralidad_Grado': round(degree_centrality.get(node, 0), 6),
                'Centralidad_Intermediacion': round(betweenness_centrality.get(node, 0), 6),
                'Centralidad_Cercania': round(closeness_centrality.get(node, 0), 6),
                'Coeficiente_Agrupamiento': round(clustering_coefficient.get(node, 0), 6),
                'Grado_Nodo': G.degree(node)
            })
        
        return residue_data
    
    @staticmethod
    def normalize_ic50_to_nm(ic50_value: float, ic50_unit: str) -> float:
        """
        Normaliza valores de IC50 a nanomolar (nM).
        
        Args:
            ic50_value: Valor de IC50
            ic50_unit: Unidad del IC50
            
        Returns:
            Valor en nM
        """
        if not ic50_value or not ic50_unit:
            return None
        
        unit_lower = ic50_unit.lower()
        if unit_lower == "nm":
            return ic50_value
        elif unit_lower in ["μm", "um"]:
            return ic50_value * 1000
        elif unit_lower == "mm":
            return ic50_value * 1000000
        else:
            return ic50_value
