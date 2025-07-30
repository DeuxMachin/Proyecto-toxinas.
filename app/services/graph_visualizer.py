"""
Servicio para visualización de grafos de proteínas.
Este módulo maneja la creación de visualizaciones interactivas con Plotly.
"""

import numpy as np
from graphein.protein.visualisation import plotly_protein_structure_graph
from typing import Dict, Any


class GraphVisualizer:
    """Clase para visualización de grafos de proteínas."""
    
    @staticmethod
    def create_plotly_visualization(G, granularity: str, protein_id: int) -> Dict[str, Any]:
        """
        Crea una visualización interactiva del grafo usando Plotly.
        
        Args:
            G: Grafo de NetworkX
            granularity: Granularidad del grafo ('atom' o 'CA')
            protein_id: ID de la proteína
            
        Returns:
            Figura de Plotly serializada
        """
        # Definir título según la granularidad
        if granularity == 'atom':
            plot_title = f"Grafo de Átomos (ID: {protein_id})"
        else:
            plot_title = f"Grafo de CA (ID: {protein_id})"
        
        # Crear la figura con Graphein
        fig = plotly_protein_structure_graph(
            G,
            colour_nodes_by="seq_position",
            colour_edges_by="kind",
            label_node_ids=False,
            node_size_multiplier=0,
            plot_title=plot_title
        )
        
        return fig
    
    @staticmethod
    def configure_plot_layout(fig) -> None:
        """
        Configura el layout y estilo de la visualización.
        
        Args:
            fig: Figura de Plotly a configurar
        """
        fig.update_layout(
            scene=dict(
                xaxis=dict(
                    title='X', 
                    showgrid=True, 
                    zeroline=True, 
                    backgroundcolor='rgba(240,240,240,0.9)', 
                    showbackground=True, 
                    gridcolor='lightgray', 
                    showticklabels=True, 
                    tickfont=dict(size=10)
                ),
                yaxis=dict(
                    title='Y', 
                    showgrid=True, 
                    zeroline=True, 
                    backgroundcolor='rgba(240,240,240,0.9)', 
                    showbackground=True, 
                    gridcolor='lightgray', 
                    showticklabels=True, 
                    tickfont=dict(size=10)
                ),
                zaxis=dict(
                    title='Z', 
                    showgrid=True, 
                    zeroline=True, 
                    backgroundcolor='rgba(240,240,240,0.9)', 
                    showbackground=True, 
                    gridcolor='lightgray', 
                    showticklabels=True, 
                    tickfont=dict(size=10)
                ),
                aspectmode='data',
                bgcolor='white'
            ),
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=True,
            legend=dict(
                x=0.85, 
                y=0.9, 
                bgcolor='rgba(255,255,255,0.5)', 
                bordercolor='black', 
                borderwidth=1
            )
        )
    
    @staticmethod
    def style_plot_traces(fig, granularity: str) -> None:
        """
        Aplica estilos a las trazas del gráfico.
        
        Args:
            fig: Figura de Plotly
            granularity: Granularidad del grafo
        """
        # Configurar opacidad y ancho de líneas
        fig.update_traces(marker=dict(opacity=0.9), selector=dict(mode='markers'))
        fig.update_traces(line=dict(width=2), selector=dict(mode='lines'))
        
        # Configurar nombres de las trazas
        for trace in fig.data:
            if trace.mode == 'markers':
                trace.name = "Residuos" if granularity == 'CA' else "Átomos"
            elif trace.mode == 'lines':
                trace.name = "Conexiones"
    
    @staticmethod
    def create_complete_visualization(G, granularity: str, protein_id: int) -> Dict[str, Any]:
        """
        Crea una visualización completa del grafo con configuración y estilo.
        
        Args:
            G: Grafo de NetworkX
            granularity: Granularidad del grafo
            protein_id: ID de la proteína
            
        Returns:
            Figura de Plotly configurada y serializada
        """
        # Crear visualización base
        fig = GraphVisualizer.create_plotly_visualization(G, granularity, protein_id)
        
        # Configurar layout
        GraphVisualizer.configure_plot_layout(fig)
        
        # Aplicar estilos
        GraphVisualizer.style_plot_traces(fig, granularity)
        
        # Serializar para JSON
        return fig.to_plotly_json()
    
    @staticmethod
    def convert_numpy_to_lists(obj):
        """
        Convierte recursivamente arrays de NumPy a listas Python para serialización JSON.
        
        Args:
            obj: Objeto que puede contener arrays de NumPy
            
        Returns:
            Objeto con arrays convertidos a listas
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: GraphVisualizer.convert_numpy_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [GraphVisualizer.convert_numpy_to_lists(i) for i in obj]
        else:
            return obj
