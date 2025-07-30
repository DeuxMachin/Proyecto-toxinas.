"""
Rutas para análisis de grafos de proteínas.
Este módulo maneja la construcción, análisis y visualización de grafos moleculares.
"""

from flask import Blueprint, jsonify, request
import tempfile
import traceback

from app.services.database_service import DatabaseService
from app.services.pdb_processor import PDBProcessor
from app.services.graph_analyzer import GraphAnalyzer
from app.services.graph_visualizer import GraphVisualizer

# Crear blueprint
graph_bp = Blueprint('graph', __name__)

# Inicializar servicios
db_service = DatabaseService()


@graph_bp.route("/get_protein_graph/<string:source>/<int:pid>")
def get_protein_graph(source, pid):
    """
    Genera y analiza el grafo molecular de una proteína.
    
    Parámetros URL:
    - long: Umbral de interacciones largas (default: 5)
    - threshold: Umbral de distancia (default: 10.0)
    - granularity: Granularidad del grafo ('CA' o 'atom', default: 'CA')
    """
    try:
        print(f"🚀 Iniciando análisis de grafo para {source}/{pid}")
        
        # Obtener parámetros de la URL
        long_threshold = int(request.args.get('long', 5))
        distance_threshold = float(request.args.get('threshold', 10.0))
        granularity = request.args.get('granularity', 'CA')
        
        # Obtener datos de la base de datos
        toxin_data = db_service.get_complete_toxin_data(source, pid)
        if not toxin_data:
            return jsonify({"error": "PDB not found"}), 404
        
        pdb_data = toxin_data['pdb_data']
        toxin_name = toxin_data['name']
        
        # Procesar PDB y crear archivo temporal
        pdb_content = PDBProcessor.bytes_to_string(pdb_data)
        processed_pdb_content = PDBProcessor.preprocess_pdb_for_graphein(pdb_content)
        
        with tempfile.NamedTemporaryFile(suffix='.pdb', delete=False) as temp_file:
            temp_file.write(processed_pdb_content.encode('utf-8'))
            temp_path = temp_file.name
        
        try:
            # Crear configuración del grafo
            config = GraphAnalyzer.create_graph_config(granularity, long_threshold, distance_threshold)
            
            # Determinar título del gráfico
            if granularity == 'atom':
                plot_title = f"Grafo de Átomos (ID: {pid})"
            else:
                plot_title = f"Grafo de CA (ID: {pid})"
            
            print(f"📊 Construyendo grafo con granularidad: {granularity}")
            
            # Construir grafo
            G = GraphAnalyzer.construct_protein_graph(temp_path, config)
            print(f"✅ Grafo construido exitosamente: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
            
            # Realizar análisis completo del grafo
            props = GraphAnalyzer.compute_complete_graph_analysis(G)
            
            # Crear visualización
            fig_json = GraphVisualizer.create_complete_visualization(G, granularity, pid)
            
            # Crear estadísticas resumidas
            summary_stats = GraphAnalyzer.create_summary_statistics(props)
            
            # Extraer top 5 residuos
            top5_residues = GraphAnalyzer.extract_top5_residues(props)
            
            # Crear payload de respuesta
            payload = {
                "plotData": fig_json["data"],
                "layout": fig_json["layout"],
                "properties": props,
                "pdb_data": pdb_content,  # Devolver el PDB original, no el procesado
                "summary_statistics": summary_stats,
                "top_5_residues": top5_residues
            }
            
            # Convertir arrays NumPy a listas para serialización JSON
            payload = GraphVisualizer.convert_numpy_to_lists(payload)
            
            print(f"📤 Enviando payload para análisis en frontend")
            return jsonify(payload)
        
        finally:
            # Limpiar archivo temporal
            PDBProcessor.cleanup_temp_files(temp_path)
    
    except Exception as e:
        print(f"💥 Error generating graph: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
