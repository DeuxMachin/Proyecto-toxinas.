"""
Servicio para análisis comparativo de toxinas.
Este módulo maneja comparaciones entre toxinas WT y de referencia.
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from app.utils.graph_segmentation import agrupar_por_segmentos_atomicos


class ToxinComparisonService:
    """Servicio para análisis comparativo de toxinas."""
    
    @staticmethod
    def get_wt_mapping() -> Dict[str, str]:
        """
        Obtiene el mapeo de familias WT a códigos de péptidos.
        
        Returns:
            Diccionario de mapeo
        """
        return {
            'μ-TRTX-Hh2a': 'μ-TRTX-Hh2a',
            'μ-TRTX-Hhn2b': 'μ-TRTX-Hhn2b',
            'β-TRTX-Cd1a': 'β-TRTX-Cd1a',
            'ω-TRTX-Gr2a': 'ω-TRTX-Gr2a'
        }
    
    @staticmethod
    def get_reference_file_path() -> str:
        """
        Obtiene la ruta del archivo de referencia.
        
        Returns:
            Ruta del archivo de referencia
        """
        return os.path.join("pdbs", "WT", "hwt4_Hh2a_WT.pdb")
    
    @staticmethod
    def validate_wt_family(wt_family: str) -> bool:
        """
        Valida si una familia WT es reconocida.
        
        Args:
            wt_family: Familia WT a validar
            
        Returns:
            True si es válida
        """
        wt_mapping = ToxinComparisonService.get_wt_mapping()
        return wt_family in wt_mapping
    
    @staticmethod
    def process_single_toxin_for_comparison(pdb_data, toxin_name: str, ic50_value: Optional[float],
                                          ic50_unit: Optional[str], granularity: str,
                                          long_threshold: int, distance_threshold: float,
                                          toxin_type: str, export_type: str = 'residues') -> Union[List[Dict], pd.DataFrame]:
        """
        Procesa una sola toxina para análisis comparativo.
        
        Args:
            pdb_data: Datos PDB
            toxin_name: Nombre de la toxina
            ic50_value: Valor de IC50
            ic50_unit: Unidad de IC50
            granularity: Granularidad del análisis
            long_threshold: Umbral de interacciones largas
            distance_threshold: Umbral de distancia
            toxin_type: Tipo de toxina ("WT_Target" o "Reference")
            export_type: Tipo de exportación ('residues' o 'segments_atomicos')
            
        Returns:
            Lista de datos o DataFrame según el tipo de exportación
        """
        from app.services.pdb_processor import PDBProcessor
        from app.services.graph_analyzer import GraphAnalyzer, ResidueAnalyzer
        import networkx as nx
        
        try:
            # Preprocesar PDB para graphein
            pdb_content = PDBProcessor.prepare_pdb_data(pdb_data)
            
            # Crear archivo temporal
            pdb_path = PDBProcessor.create_temp_pdb_file(pdb_content)
            
            try:
                # Construir grafo
                config = GraphAnalyzer.create_graph_config(granularity, long_threshold, distance_threshold)
                G = GraphAnalyzer.construct_protein_graph(pdb_path, config)
                
                print(f"    ✅ Grafo construido: {G.number_of_nodes()} nodos, {G.number_of_edges()} aristas")
                
                # Procesar según el tipo de exportación
                if export_type == 'segments_atomicos':
                    # Usar segmentación atómica
                    print(f"    🧩 Aplicando segmentación atómica para {toxin_name}...")
                    df_segmentos = agrupar_por_segmentos_atomicos(G, granularity=granularity)
                    
                    if not df_segmentos.empty:
                        # Agregar información de la toxina
                        df_segmentos['Toxina'] = toxin_name
                        df_segmentos['Tipo_Toxina'] = toxin_type
                        
                        # Agregar datos de IC50
                        if ic50_value and ic50_unit:
                            df_segmentos['IC50_Value'] = ic50_value
                            df_segmentos['IC50_Unit'] = ic50_unit
                            df_segmentos['IC50_nM'] = ResidueAnalyzer.normalize_ic50_to_nm(ic50_value, ic50_unit)
                        else:
                            df_segmentos['IC50_Value'] = None
                            df_segmentos['IC50_Unit'] = None
                            df_segmentos['IC50_nM'] = None
                        
                        # Extraer familia WT
                        from app.services.export_service import FamilyAnalysisProcessor
                        family_wt = FamilyAnalysisProcessor.determine_family_wt(toxin_name, toxin_type)
                        df_segmentos['Familia_WT'] = family_wt
                        
                        # Reordenar columnas
                        cols = ['Toxina', 'Tipo_Toxina', 'Familia_WT', 'IC50_Value', 'IC50_Unit', 'IC50_nM'] + \
                               [col for col in df_segmentos.columns if col not in ['Toxina', 'Tipo_Toxina', 'Familia_WT', 'IC50_Value', 'IC50_Unit', 'IC50_nM']]
                        df_segmentos = df_segmentos[cols]
                        
                        print(f"    ✅ Segmentación completada: {len(df_segmentos)} segmentos procesados")
                        return df_segmentos
                    else:
                        print(f"    ⚠️ No se generaron segmentos para {toxin_name}")
                        return pd.DataFrame()
                
                else:
                    # Análisis por residuos tradicional
                    print(f"    📊 Calculando métricas de centralidad para {toxin_name}...")
                    degree_centrality = nx.degree_centrality(G)
                    betweenness_centrality = nx.betweenness_centrality(G)
                    closeness_centrality = nx.closeness_centrality(G)
                    clustering_coefficient = nx.clustering(G)
                    
                    # Normalizar IC50 a unidades consistentes (nM)
                    ic50_nm = ResidueAnalyzer.normalize_ic50_to_nm(ic50_value, ic50_unit) if ic50_value and ic50_unit else None
                    
                    print(f"     IC50 normalizado: {ic50_nm} nM")
                    
                    # Extraer familia WT
                    from app.services.export_service import FamilyAnalysisProcessor
                    family_wt = FamilyAnalysisProcessor.determine_family_wt(toxin_name, toxin_type)
                    
                    # Procesar cada nodo/residuo
                    toxin_data = []
                    for node, data in G.nodes(data=True):
                        if granularity == 'CA':
                            parts = str(node).split(':')
                            if len(parts) >= 3:
                                chain = parts[0]
                                residue_name = parts[1]
                                residue_number = parts[2]
                            else:
                                chain = data.get('chain_id', 'A')
                                residue_name = data.get('residue_name', 'UNK')
                                residue_number = str(node)
                        else:  # nivel atómico
                            chain = data.get('chain_id', 'A')
                            residue_name = data.get('residue_name', 'UNK')
                            residue_number = str(data.get('residue_number', node))
                        
                        # Incluir datos esenciales y métricas
                        toxin_data.append({
                            # Identificadores
                            'Toxina': toxin_name,
                            'Tipo_Toxina': toxin_type,
                            'Familia_WT': family_wt,
                            'Cadena': chain,
                            'Residuo_Nombre': residue_name,
                            'Residuo_Numero': residue_number,
                            
                            # Información de IC50
                            'IC50_Value': ic50_value,
                            'IC50_Unit': ic50_unit,
                            'IC50_nM': ic50_nm,
                            
                            # Métricas de centralidad
                            'Centralidad_Grado': round(degree_centrality.get(node, 0), 6),
                            'Centralidad_Intermediacion': round(betweenness_centrality.get(node, 0), 6),
                            'Centralidad_Cercania': round(closeness_centrality.get(node, 0), 6),
                            'Coeficiente_Agrupamiento': round(clustering_coefficient.get(node, 0), 6),
                            
                            # Propiedades estructurales
                            'Grado_Nodo': G.degree(node)
                        })
                    
                    print(f"     ✅ Procesados {len(toxin_data)} residuos de {toxin_name}")
                    return toxin_data
                
            finally:
                PDBProcessor.cleanup_temp_files(pdb_path)
                print(f"     Archivo temporal eliminado")
                
        except Exception as e:
            print(f"     Error procesando {toxin_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return [] if export_type != 'segments_atomicos' else pd.DataFrame()
    
    @staticmethod
    def load_reference_toxin(reference_path: str) -> Optional[str]:
        """
        Carga la toxina de referencia desde archivo.
        
        Args:
            reference_path: Ruta del archivo de referencia
            
        Returns:
            Contenido del archivo o None si no existe
        """
        if not os.path.exists(reference_path):
            return None
        
        try:
            with open(reference_path, 'r') as ref_file:
                return ref_file.read()
        except Exception as e:
            print(f"Error cargando archivo de referencia: {e}")
            return None
