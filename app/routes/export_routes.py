"""
Rutas para exportación de datos de análisis.
Este módulo maneja todas las exportaciones a Excel y CSV.
"""

from flask import Blueprint, jsonify, request, send_file
import traceback
import pandas as pd
import networkx as nx

from app.services.database_service import DatabaseService
from app.services.pdb_processor import PDBProcessor, FileUtils
from app.services.graph_analyzer import GraphAnalyzer, ResidueAnalyzer
from app.services.export_service import ExportService
from app.utils.graph_segmentation import agrupar_por_segmentos_atomicos

# Crear blueprint
export_bp = Blueprint('export', __name__)

# Inicializar servicios
db_service = DatabaseService()


@export_bp.route("/export_residues_xlsx/<string:source>/<int:pid>")
def export_residues_xlsx(source, pid):
    """
    Exporta análisis de residuos de una toxina específica a Excel.
    
    Parámetros URL:
    - long: Umbral de interacciones largas (default: 5)
    - threshold: Umbral de distancia (default: 10.0)  
    - granularity: Granularidad del grafo ('CA' o 'atom', default: 'CA')
    """
    try:
        # Obtener parámetros
        long_threshold = int(request.args.get('long', 5))
        distance_threshold = float(request.args.get('threshold', 10.0))
        granularity = request.args.get('granularity', 'CA')
        
        # Obtener datos completos de la toxina
        toxin_data = db_service.get_complete_toxin_data(source, pid)
        if not toxin_data:
            return jsonify({"error": "PDB not found"}), 404
        
        pdb_data = toxin_data['pdb_data']
        toxin_name = toxin_data['name']
        ic50_value = toxin_data['ic50_value']
        ic50_unit = toxin_data['ic50_unit']
        
        # Usar nombre por defecto si no existe
        if not toxin_name:
            toxin_name = f"{source}_{pid}"
        
        # Crear archivo temporal
        pdb_content = PDBProcessor.prepare_pdb_data(pdb_data)
        pdb_path = PDBProcessor.create_temp_pdb_file(pdb_content)
        
        try:
            # Construir grafo
            config = GraphAnalyzer.create_graph_config(granularity, long_threshold, distance_threshold)
            G = GraphAnalyzer.construct_protein_graph(pdb_path, config)
            
            print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
            
            # Preparar datos para exportación
            residue_data = ExportService.prepare_residue_export_data(
                G, toxin_name, ic50_value, ic50_unit, granularity
            )
            
            # Crear metadatos
            metadata = ExportService.create_metadata(
                toxin_name, source, pid, granularity, distance_threshold, 
                long_threshold, G, ic50_value, ic50_unit
            )
            
            # Generar archivo Excel
            excel_data, excel_filename = ExportService.generate_single_toxin_excel(
                residue_data, metadata, toxin_name, source
            )
            
            # Retornar archivo
            return send_file(
                excel_data,
                as_attachment=True,
                download_name=excel_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        finally:
            PDBProcessor.cleanup_temp_files(pdb_path)
            print("Temporary file removed")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@export_bp.route("/export_segments_atomicos_xlsx/<string:source>/<int:pid>")
def export_segments_atomicos_xlsx(source, pid):
    """
    Exporta segmentación atómica de una toxina Nav1.7 a Excel.
    Solo disponible para toxinas Nav1.7 con granularidad atómica.
    """
    try:
        # Solo permitir para Nav1.7
        if source != "nav1_7":
            return jsonify({"error": "La segmentación atómica solo está disponible para toxinas Nav1.7"}), 400
        
        # Obtener parámetros
        long_threshold = int(request.args.get('long', 5))
        distance_threshold = float(request.args.get('threshold', 10.0))
        granularity = request.args.get('granularity', 'atom')
        
        # Validar granularidad
        if granularity != 'atom':
            return jsonify({"error": "La segmentación atómica requiere granularidad 'atom'"}), 400
        
        print(f"🚀 Iniciando exportación de segmentos atómicos para Nav1.7 ID: {pid}")
        
        # Obtener datos de la toxina
        toxin_data = db_service.get_complete_toxin_data(source, pid)
        if not toxin_data:
            return jsonify({"error": "Toxina Nav1.7 no encontrada"}), 404
        
        pdb_data = toxin_data['pdb_data']
        toxin_name = toxin_data['name']
        ic50_value = toxin_data['ic50_value']
        ic50_unit = toxin_data['ic50_unit']
        
        if not toxin_name:
            toxin_name = f"Nav1.7_{pid}"
        
        print(f"📊 Procesando {toxin_name}")
        
        # Crear archivo temporal
        pdb_content = PDBProcessor.prepare_pdb_data(pdb_data)
        pdb_path = PDBProcessor.create_temp_pdb_file(pdb_content)
        
        try:
            # Construir grafo atómico
            config = GraphAnalyzer.create_graph_config(granularity, long_threshold, distance_threshold)
            G = GraphAnalyzer.construct_protein_graph(pdb_path, config)
            
            print(f"✅ Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
            
            if G.number_of_nodes() == 0:
                return jsonify({"error": "El grafo no tiene nodos"}), 500
            
            # Aplicar segmentación atómica
            print(f"🧩 Aplicando segmentación atómica...")
            df_segmentos = agrupar_por_segmentos_atomicos(G, granularity)
            
            if df_segmentos.empty:
                return jsonify({"error": "No se generaron segmentos"}), 500
            
            # Agregar información de la toxina
            df_segmentos.insert(0, 'Toxina', toxin_name)
            
            print(f"📈 Segmentación completada: {len(df_segmentos)} segmentos generados")
            
            # Crear metadatos específicos para segmentación atómica
            metadata = {
                'Toxina': toxin_name,
                'Fuente': 'Nav1.7',
                'ID': pid,
                'Tipo_Analisis': 'Segmentación Atómica',
                'Granularidad': 'atom',
                'Umbral_Distancia': distance_threshold,
                'Umbral_Interaccion_Larga': long_threshold,
                'Total_Atomos_Grafo': G.number_of_nodes(),
                'Total_Conexiones_Grafo': G.number_of_edges(),
                'Densidad_Grafo': round(nx.density(G), 6),
                'Numero_Segmentos': len(df_segmentos),
                'Fecha_Exportacion': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Agregar datos de IC50 si están disponibles
            if ic50_value:
                metadata['IC50_Original'] = ic50_value
                metadata['Unidad_IC50'] = ic50_unit
            
            # Generar nombre de archivo
            clean_name = FileUtils.clean_filename(toxin_name)
            filename_prefix = f"Nav1.7-{clean_name}-Segmentos-Atomicos"
            
            print(f"💾 Generando Excel: {filename_prefix}")
            
            # Generar Excel
            from app.utils.excel_export import generate_excel
            excel_data, excel_filename = generate_excel(df_segmentos, filename_prefix, metadata=metadata)
            
            print(f"📁 Archivo Excel generado: {excel_filename}")
            
            # Retornar archivo
            return send_file(
                excel_data,
                as_attachment=True,
                download_name=excel_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        finally:
            PDBProcessor.cleanup_temp_files(pdb_path)
            print("🗑️  Archivo temporal eliminado")
    
    except Exception as e:
        print(f"❌ Error en export_segments_atomicos_xlsx: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@export_bp.route("/export_family_xlsx/<string:family_prefix>")
def export_family_xlsx(family_prefix):
    """
    Exporta análisis completo de una familia de toxinas a Excel.
    
    Parámetros URL:
    - long: Umbral de interacciones largas (default: 5)
    - threshold: Umbral de distancia (default: 10.0)
    - granularity: Granularidad del grafo ('CA' o 'atom', default: 'CA')
    - export_type: Tipo de exportación ('residues' o 'segments_atomicos', default: 'residues')
    """
    try:
        # Obtener parámetros
        long_threshold = int(request.args.get('long', 5))
        distance_threshold = float(request.args.get('threshold', 10.0))
        granularity = request.args.get('granularity', 'CA')
        export_type = request.args.get('export_type', 'residues')
        
        print(f"Procesando familia {family_prefix} con parámetros: long={long_threshold}, dist={distance_threshold}, granularity={granularity}, tipo={export_type}")
        
        # Validación para segmentación atómica
        if export_type == 'segments_atomicos' and granularity != 'atom':
            return jsonify({"error": "La segmentación atómica requiere granularidad 'atom'"}), 400
        
        # Obtener toxinas de esta familia
        family_toxins = db_service.get_family_toxins(family_prefix)
        
        if not family_toxins:
            return jsonify({"error": f"No se encontraron toxinas para la familia {family_prefix}"}), 404
        
        print(f"Procesando familia {family_prefix}: {len(family_toxins)} toxinas encontradas")
        
        # Procesar cada toxina de la familia
        toxin_dataframes = {}
        processed_count = 0
        
        # Crear metadatos para la familia completa
        from datetime import datetime
        metadata = {
            'Familia': family_prefix,
            'Tipo_Analisis': 'Segmentación Atómica' if export_type == 'segments_atomicos' else 'Análisis por Residuos',
            'Numero_Toxinas_Procesadas': len(family_toxins),
            'Umbral_Distancia': distance_threshold,
            'Umbral_Interaccion_Larga': long_threshold,
            'Granularidad': granularity,
            'Fecha_Exportacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Información de IC50 para metadatos
        toxin_ic50_data = {}
        
        for toxin_id, peptide_code, ic50_value, ic50_unit in family_toxins:
            print(f"Procesando {peptide_code} (IC₅₀: {ic50_value} {ic50_unit})")
            
            try:
                # Obtener datos PDB
                pdb_data = db_service.get_pdb_data('nav1_7', toxin_id)
                
                if not pdb_data:
                    print(f"No hay datos PDB para {peptide_code}")
                    continue
                
                print(f"PDB obtenido para {peptide_code}")
                
                # Crear archivo temporal
                pdb_content = PDBProcessor.prepare_pdb_data(pdb_data)
                pdb_path = PDBProcessor.create_temp_pdb_file(pdb_content)
                
                try:
                    # Construir grafo
                    config = GraphAnalyzer.create_graph_config(granularity, long_threshold, distance_threshold)
                    G = GraphAnalyzer.construct_protein_graph(pdb_path, config)
                    
                    print(f"Grafo construido para {peptide_code}: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
                    
                    if export_type == 'segments_atomicos':
                        # Segmentación atómica
                        df_segmentos = agrupar_por_segmentos_atomicos(G, granularity)
                        if not df_segmentos.empty:
                            df_segmentos.insert(0, 'Toxina', peptide_code)
                            df_segmentos['IC50_Value'] = ic50_value
                            df_segmentos['IC50_Unit'] = ic50_unit
                            
                            clean_peptide_code = FileUtils.clean_filename(peptide_code)
                            toxin_dataframes[clean_peptide_code] = df_segmentos
                            processed_count += 1
                    else:
                        # Análisis por residuos tradicional
                        residue_data = ExportService.prepare_residue_export_data(
                            G, peptide_code, ic50_value, ic50_unit, granularity
                        )
                        
                        if residue_data:
                            df = pd.DataFrame(residue_data)
                            clean_peptide_code = FileUtils.clean_filename(peptide_code)
                            toxin_dataframes[clean_peptide_code] = df
                            processed_count += 1
                    
                    # Agregar información del grafo a metadatos
                    metadata[f'Nodos_en_{peptide_code}'] = G.number_of_nodes()
                    metadata[f'Aristas_en_{peptide_code}'] = G.number_of_edges()
                    metadata[f'Densidad_en_{peptide_code}'] = round(nx.density(G), 6)
                    
                    # Agregar datos de IC50
                    if ic50_value:
                        toxin_ic50_data[f'IC50_{peptide_code}'] = f"{ic50_value} {ic50_unit}"
                
                finally:
                    PDBProcessor.cleanup_temp_files(pdb_path)
                
            except Exception as e:
                print(f"Error procesando toxina {peptide_code}: {str(e)}")
                traceback.print_exc()
        
        # Agregar información de IC50 a metadatos
        metadata.update(toxin_ic50_data)
        
        if not toxin_dataframes:
            return jsonify({"error": "No se pudieron procesar toxinas válidas"}), 500
        
        # Generar archivo Excel
        excel_data, excel_filename = ExportService.generate_family_excel(
            toxin_dataframes, family_prefix, metadata, export_type, granularity
        )
        
        print(f"Dataset completo generado: {processed_count} toxinas procesadas")
        
        # Devolver el archivo Excel
        return send_file(
            excel_data,
            as_attachment=True,
            download_name=excel_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@export_bp.route("/export_wt_comparison_xlsx/<string:wt_family>")
def export_wt_comparison_xlsx(wt_family):
    """
    Exporta comparación entre toxina WT y referencia a Excel.
    
    Parámetros URL:
    - long: Umbral de interacciones largas (default: 5)
    - threshold: Umbral de distancia (default: 10.0)
    - granularity: Granularidad del grafo ('CA' o 'atom', default: 'CA')
    - export_type: Tipo de exportación ('residues' o 'segments_atomicos', default: 'residues')
    """
    try:
        import os
        
        # Obtener parámetros
        long_threshold = int(request.args.get('long', 5))
        distance_threshold = float(request.args.get('threshold', 10.0))
        granularity = request.args.get('granularity', 'CA')
        export_type = request.args.get('export_type', 'residues')
        
        print(f"Procesando comparación WT para {wt_family} con parámetros: long={long_threshold}, dist={distance_threshold}, granularity={granularity}, tipo={export_type}")
        
        # Validación para segmentación atómica
        if export_type == 'segments_atomicos' and granularity != 'atom':
            return jsonify({"error": "La segmentación atómica requiere granularidad 'atom'"}), 400
        
        # Mapeo de familias WT a códigos peptídicos
        wt_mapping = {
            'μ-TRTX-Hh2a': 'μ-TRTX-Hh2a',
            'μ-TRTX-Hhn2b': 'μ-TRTX-Hhn2b',
            'β-TRTX-Cd1a': 'β-TRTX-Cd1a',
            'ω-TRTX-Gr2a': 'ω-TRTX-Gr2a'
        }
        
        if wt_family not in wt_mapping:
            return jsonify({"error": f"Familia WT no reconocida: {wt_family}"}), 400
        
        wt_peptide_code = wt_mapping[wt_family]
        
        # Obtener datos de la toxina WT desde la base de datos
        wt_toxin_data = db_service.get_wt_toxin_data(wt_peptide_code)
        if not wt_toxin_data:
            return jsonify({"error": f"Toxina WT no encontrada: {wt_peptide_code}"}), 404
        
        wt_id = wt_toxin_data['id']
        wt_code = wt_toxin_data['name']
        wt_ic50 = wt_toxin_data['ic50_value']
        wt_unit = wt_toxin_data['ic50_unit']
        wt_pdb_data = wt_toxin_data['pdb_data']
        
        print(f"Toxina WT encontrada: {wt_code} (IC₅₀: {wt_ic50} {wt_unit})")
        
        # Cargar toxina de referencia desde archivo local
        reference_path = os.path.join("pdbs", "WT", "hwt4_Hh2a_WT.pdb")
        if not os.path.exists(reference_path):
            return jsonify({"error": f"Archivo de referencia no encontrado: {reference_path}"}), 404
        
        print(f"Archivo de referencia encontrado: {reference_path}")
        
        # Procesar ambas toxinas
        comparison_dataframes = {}
        
        # Crear metadatos
        from datetime import datetime
        metadata = {
            'Toxina_WT': wt_code,
            'Toxina_Referencia': 'hwt4_Hh2a_WT',
            'Familia': wt_family,
            'Tipo_Analisis': 'Segmentación Atómica' if export_type == 'segments_atomicos' else 'Análisis por Residuos',
            'IC50_WT': f"{wt_ic50} {wt_unit}" if wt_ic50 and wt_unit else "No disponible",
            'Granularidad': granularity,
            'Umbral_Distancia': distance_threshold,
            'Umbral_Interaccion_Larga': long_threshold,
            'Fecha_Exportacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # === PROCESAR TOXINA WT ===
        print(f"Procesando toxina WT: {wt_code}")
        wt_data = process_single_toxin_for_comparison(
            pdb_data=wt_pdb_data,
            toxin_name=wt_code,
            ic50_value=wt_ic50,
            ic50_unit=wt_unit,
            granularity=granularity,
            long_threshold=long_threshold,
            distance_threshold=distance_threshold,
            toxin_type="WT_Target",
            export_type=export_type
        )
        
        if wt_data is not None:
            if export_type == 'segments_atomicos':
                # Para segmentación atómica, wt_data ya es un DataFrame
                comparison_dataframes['WT_Target'] = wt_data
            else:
                # Para residuos, convertir a DataFrame
                wt_df = pd.DataFrame(wt_data)
                comparison_dataframes['WT_Target'] = wt_df
        
        # === PROCESAR TOXINA DE REFERENCIA ===
        print(f"Procesando toxina de referencia: hwt4_Hh2a_WT")
        with open(reference_path, 'r') as ref_file:
            ref_pdb_content = ref_file.read()
        
        ref_data = process_single_toxin_for_comparison(
            pdb_data=ref_pdb_content,
            toxin_name="hwt4_Hh2a_WT",
            ic50_value=None,
            ic50_unit=None,
            granularity=granularity,
            long_threshold=long_threshold,
            distance_threshold=distance_threshold,
            toxin_type="Reference",
            export_type=export_type
        )
        
        if ref_data is not None:
            if export_type == 'segments_atomicos':
                # Para segmentación atómica, ref_data ya es un DataFrame
                comparison_dataframes['Reference'] = ref_data
            else:
                # Para residuos, convertir a DataFrame
                ref_df = pd.DataFrame(ref_data)
                comparison_dataframes['Reference'] = ref_df
        
        # Crear hoja de resumen si ambas toxinas fueron procesadas
        if 'WT_Target' in comparison_dataframes and 'Reference' in comparison_dataframes:
            wt_df = comparison_dataframes['WT_Target']
            ref_df = comparison_dataframes['Reference']
            
            if export_type == 'segments_atomicos':
                # Resumen para segmentación atómica
                summary_data = {
                    'Propiedad': [
                        'Toxina WT', 'Toxina Referencia',
                        'Número de Segmentos',
                        'Promedio Átomos por Segmento',
                        'Promedio Conexiones Internas',
                        'Promedio Densidad Segmento',
                        'Promedio Centralidad Grado',
                        'Promedio Centralidad Intermediación',
                        'Promedio Centralidad Cercanía',
                        'Promedio Coeficiente Agrupamiento'
                    ],
                    'WT_Target': [
                        wt_code, 'N/A',
                        len(wt_df),
                        wt_df['Num_Atomos'].mean(),
                        wt_df['Conexiones_Internas'].mean(),
                        wt_df['Densidad_Segmento'].mean(),
                        wt_df['Centralidad_Grado_Promedio'].mean(),
                        wt_df['Centralidad_Intermediacion_Promedio'].mean(),
                        wt_df['Centralidad_Cercania_Promedio'].mean(),
                        wt_df['Coeficiente_Agrupamiento_Promedio'].mean()
                    ],
                    'Reference': [
                        'N/A', 'hwt4_Hh2a_WT',
                        len(ref_df),
                        ref_df['Num_Atomos'].mean(),
                        ref_df['Conexiones_Internas'].mean(),
                        ref_df['Densidad_Segmento'].mean(),
                        ref_df['Centralidad_Grado_Promedio'].mean(),
                        ref_df['Centralidad_Intermediacion_Promedio'].mean(),
                        ref_df['Centralidad_Cercania_Promedio'].mean(),
                        ref_df['Coeficiente_Agrupamiento_Promedio'].mean()
                    ]
                }
            else:
                # Resumen para análisis por residuos
                summary_data = {
                    'Propiedad': [
                        'Toxina WT', 'Toxina Referencia',
                        'Número de Residuos',
                        'Centralidad Grado Promedio',
                        'Centralidad Intermediación Promedio',
                        'Centralidad Cercanía Promedio',
                        'Coeficiente Agrupamiento Promedio'
                    ],
                    'WT_Target': [
                        wt_code, 'N/A',
                        len(wt_df),
                        wt_df['Centralidad_Grado'].mean(),
                        wt_df['Centralidad_Intermediacion'].mean(),
                        wt_df['Centralidad_Cercania'].mean(),
                        wt_df['Coeficiente_Agrupamiento'].mean()
                    ],
                    'Reference': [
                        'N/A', 'hwt4_Hh2a_WT',
                        len(ref_df),
                        ref_df['Centralidad_Grado'].mean(),
                        ref_df['Centralidad_Intermediacion'].mean(),
                        ref_df['Centralidad_Cercania'].mean(),
                        ref_df['Coeficiente_Agrupamiento'].mean()
                    ]
                }
            
            comparison_dataframes['Resumen_Comparativo'] = pd.DataFrame(summary_data)
        
        # Generar archivo Excel
        family_clean = FileUtils.clean_filename(wt_family)
        analysis_type = "SegmentosAtomicos" if export_type == 'segments_atomicos' else "Residuos"
        filename_prefix = f"Comparacion_WT_{family_clean}_vs_hwt4_Hh2a_WT_{analysis_type}_{granularity}"
        
        from app.utils.excel_export import generate_excel
        excel_data, excel_filename = generate_excel(comparison_dataframes, filename_prefix, metadata=metadata)
        
        # Retornar el archivo Excel
        return send_file(
            excel_data,
            as_attachment=True,
            download_name=excel_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def process_single_toxin_for_comparison(pdb_data, toxin_name, ic50_value, ic50_unit, granularity, long_threshold, distance_threshold, toxin_type, export_type='residues'):
    """
    Procesa una sola toxina para análisis comparativo.
    Soporta tanto análisis por residuos como segmentación atómica.
    
    Args:
        pdb_data: Datos PDB (bytes o string)
        toxin_name: Nombre de la toxina
        ic50_value: Valor de IC50
        ic50_unit: Unidad de IC50
        granularity: Granularidad del grafo
        long_threshold: Umbral de interacciones largas
        distance_threshold: Umbral de distancia
        toxin_type: Tipo de toxina ("WT_Target" o "Reference")
        export_type: Tipo de exportación ('residues' o 'segments_atomicos')
    
    Returns:
        DataFrame o lista de datos según el tipo de exportación
    """
    try:
        # Crear archivo temporal
        pdb_content = PDBProcessor.prepare_pdb_data(pdb_data)
        pdb_path = PDBProcessor.create_temp_pdb_file(pdb_content)
        
        try:
            # Construir grafo
            config = GraphAnalyzer.create_graph_config(granularity, long_threshold, distance_threshold)
            G = GraphAnalyzer.construct_protein_graph(pdb_path, config)
            
            print(f"    ✅ Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
            
            if export_type == 'segments_atomicos':
                # Segmentación atómica
                print(f"    🧩 Aplicando segmentación atómica...")
                df_segmentos = agrupar_por_segmentos_atomicos(G, granularity)
                
                if df_segmentos.empty:
                    print(f"    ⚠️ No se generaron segmentos para {toxin_name}")
                    return None
                
                # Agregar información de la toxina
                df_segmentos.insert(0, 'Toxina', toxin_name)
                df_segmentos['Tipo'] = toxin_type
                
                if ic50_value and ic50_unit:
                    df_segmentos['IC50_Value'] = ic50_value
                    df_segmentos['IC50_Unit'] = ic50_unit
                else:
                    df_segmentos['IC50_Value'] = None
                    df_segmentos['IC50_Unit'] = None
                
                print(f"     Procesados {len(df_segmentos)} segmentos de {toxin_name}")
                return df_segmentos
                
            else:
                # Análisis por residuos tradicional
                print(f"    📊 Calculando métricas por residuos...")
                residue_data = ExportService.prepare_residue_export_data(
                    G, toxin_name, ic50_value, ic50_unit, granularity
                )
                
                if not residue_data:
                    print(f"    ⚠️ No se generaron datos de residuos para {toxin_name}")
                    return None
                
                # Agregar tipo de toxina a cada residuo
                for residue in residue_data:
                    residue['Tipo'] = toxin_type
                
                print(f"     Procesados {len(residue_data)} residuos de {toxin_name}")
                return residue_data
            
        finally:
            PDBProcessor.cleanup_temp_files(pdb_path)
            
    except Exception as e:
        print(f"     Error procesando {toxin_name}: {str(e)}")
        traceback.print_exc()
        return None
    