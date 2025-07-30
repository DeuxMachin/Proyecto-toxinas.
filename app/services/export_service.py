"""
Servicio para exportación de datos de análisis de grafos de proteínas.
Este módulo maneja la generación de archivos Excel y CSV con datos de análisis.
"""

import pandas as pd
import networkx as nx
import unicodedata
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import os
import sys

# Agregar path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.utils.excel_export import generate_excel


class ExportUtils:
    """Utilidades para exportación."""
    
    @staticmethod
    def clean_filename(name: str, max_length: int = 31) -> str:
        """Limpia un nombre para usarlo como nombre de archivo."""
        # Normalizar Unicode
        normalized_name = unicodedata.normalize('NFKD', name)
        
        # Convertir caracteres griegos especiales a ASCII
        clean_name = (normalized_name
                     .replace('μ', 'mu')
                     .replace('β', 'beta')
                     .replace('ω', 'omega')
                     .replace('δ', 'delta'))
        
        # Remover caracteres no ASCII alfanuméricos, guiones o guiones bajos
        clean_name = re.sub(r'[^\w\-_]', '', clean_name, flags=re.ASCII)
        
        # Truncar si es necesario
        if len(clean_name) > max_length:
            clean_name = clean_name[:max_length]
        
        return clean_name if clean_name else "unknown"
    
    @staticmethod
    def normalize_ic50_to_nm(ic50_value: float, ic50_unit: str) -> float:
        """Normaliza valores de IC50 a nanomolar (nM)."""
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
    
    @staticmethod
    def extract_residue_data(G, granularity: str) -> List[Dict[str, Any]]:
        """Extrae datos de residuos del grafo para exportación."""
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


class ExportService:
    """Servicio para exportación de datos de análisis."""
    
    @staticmethod
    def prepare_residue_export_data(G, toxin_name: str, ic50_value: Optional[float] = None, 
                                   ic50_unit: Optional[str] = None, granularity: str = 'CA') -> List[Dict[str, Any]]:
        """Prepara datos de residuos para exportación."""
        # Extraer datos básicos de residuos
        residue_data = ExportUtils.extract_residue_data(G, granularity)
        
        # Agregar información de toxina e IC50
        for residue in residue_data:
            residue['Toxina'] = toxin_name
            
            if ic50_value and ic50_unit:
                residue['IC50_Value'] = ic50_value
                residue['IC50_Unit'] = ic50_unit
                # Normalizar a nM
                residue['IC50_nM'] = ExportUtils.normalize_ic50_to_nm(ic50_value, ic50_unit)
        
        return residue_data
    
    @staticmethod
    def create_metadata(toxin_name: str, source: str, protein_id: int, granularity: str,
                       distance_threshold: float, long_threshold: int, G,
                       ic50_value: Optional[float] = None, ic50_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea metadatos para la exportación.
        
        Args:
            toxin_name: Nombre de la toxina
            source: Fuente de datos
            protein_id: ID de la proteína
            granularity: Granularidad del análisis
            distance_threshold: Umbral de distancia usado
            long_threshold: Umbral de interacciones largas usado
            G: Grafo analizado
            ic50_value: Valor de IC50 (opcional)
            ic50_unit: Unidad de IC50 (opcional)
            
        Returns:
            Diccionario de metadatos
        """
        import networkx as nx
        
        metadata = {
            'Toxina': toxin_name,
            'Fuente': source,
            'ID': protein_id,
            'Granularidad': granularity,
            'Umbral_Distancia': distance_threshold,
            'Umbral_Interaccion_Larga': long_threshold,
            'Densidad_del_grafo': round(nx.density(G), 6),
            'Numero_de_nodos': G.number_of_nodes(),
            'Numero_de_aristas': G.number_of_edges(),
            'Fecha_Exportacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Agregar datos de IC50 si están disponibles
        if ic50_value and ic50_unit:
            metadata['IC50_Original'] = ic50_value
            metadata['Unidad_IC50'] = ic50_unit
            metadata['IC50_nM'] = ExportUtils.normalize_ic50_to_nm(ic50_value, ic50_unit)
        
        return metadata
    
    @staticmethod
    def generate_single_toxin_excel(residue_data: List[Dict], metadata: Dict[str, Any], 
                                   toxin_name: str, source: str) -> tuple:
        """
        Genera archivo Excel para una sola toxina.
        
        Args:
            residue_data: Datos de residuos
            metadata: Metadatos del análisis
            toxin_name: Nombre de la toxina
            source: Fuente de datos
            
        Returns:
            Tupla (archivo_excel, nombre_archivo)
        """
        # Crear DataFrame
        df = pd.DataFrame(residue_data)
        
        # Limpiar nombre para archivo
        clean_name = ExportUtils.clean_filename(toxin_name)
        
        # Generar nombre de archivo
        if source == "nav1_7":
            filename_prefix = f"Nav1.7-{clean_name}"
        else:
            filename_prefix = f"Toxinas-{clean_name}"
        
        # Generar Excel
        return generate_excel(df, filename_prefix, metadata=metadata)
    
    @staticmethod
    def generate_family_excel(toxin_dataframes: Dict[str, pd.DataFrame], family_prefix: str,
                             metadata: Dict[str, Any], export_type: str = 'residues',
                             granularity: str = 'CA') -> tuple:
        """
        Genera archivo Excel para una familia de toxinas.
        
        Args:
            toxin_dataframes: Diccionario de DataFrames por toxina
            family_prefix: Prefijo de la familia
            metadata: Metadatos del análisis
            export_type: Tipo de exportación ('residues' o 'segments_atomicos')
            granularity: Granularidad del análisis
            
        Returns:
            Tupla (archivo_excel, nombre_archivo)
        """
        # Mapeo de nombres de familias
        family_names = {
            'μ': 'Mu-TRTX',
            'β': 'Beta-TRTX', 
            'ω': 'Omega-TRTX',
        }
        
        family_name = family_names.get(family_prefix, f"{family_prefix}-TRTX")
        
        # Ajustar nombre según tipo de análisis
        if export_type == 'segments_atomicos':
            filename_prefix = f"Dataset_Familia_{family_name}_Segmentacion_Atomica_{granularity}"
        else:
            filename_prefix = f"Dataset_Familia_{family_name}_IC50_Topologia_{granularity}"
        
        # Generar Excel con múltiples hojas
        return generate_excel(toxin_dataframes, filename_prefix, metadata=metadata)
    
    @staticmethod
    def generate_comparison_excel(comparison_dataframes: Dict[str, pd.DataFrame], 
                                 wt_family: str, metadata: Dict[str, Any],
                                 export_type: str = 'residues', granularity: str = 'CA') -> tuple:
        """
        Genera archivo Excel para comparación WT.
        
        Args:
            comparison_dataframes: DataFrames de comparación
            wt_family: Familia WT
            metadata: Metadatos del análisis
            export_type: Tipo de exportación
            granularity: Granularidad del análisis
            
        Returns:
            Tupla (archivo_excel, nombre_archivo)
        """
        family_clean = (wt_family.replace('μ', 'mu')
                               .replace('β', 'beta')
                               .replace('ω', 'omega')
                               .replace('δ', 'delta'))
        
        if export_type == 'segments_atomicos':
            filename_prefix = f"Comparacion_WT_{family_clean}_vs_hwt4_Hh2a_WT_Segmentacion_Atomica_{granularity}"
        else:
            filename_prefix = f"Comparacion_WT_{family_clean}_vs_hwt4_Hh2a_WT_{granularity}"
        
        return generate_excel(comparison_dataframes, filename_prefix, metadata=metadata)
    
    @staticmethod
    def create_summary_comparison_dataframe(wt_df: pd.DataFrame, ref_df: pd.DataFrame,
                                          wt_code: str, export_type: str = 'residues') -> pd.DataFrame:
        """
        Crea DataFrame de resumen comparativo entre toxinas WT y referencia.
        
        Args:
            wt_df: DataFrame de toxina WT
            ref_df: DataFrame de toxina de referencia
            wt_code: Código de la toxina WT
            export_type: Tipo de exportación
            
        Returns:
            DataFrame de resumen comparativo
        """
        if export_type == 'segments_atomicos':
            # Para segmentación atómica, usar métricas específicas
            summary_data = {
                'Propiedad': [
                    'Toxina_WT', 'Toxina_Referencia',
                    'Numero_Segmentos_Atomicos', 
                    'Conexiones_Internas_Promedio',
                    'Densidad_Segmento_Promedio', 
                    'Centralidad_Grado_Promedio',
                    'Centralidad_Intermediacion_Promedio'
                ],
                'WT_Target': [
                    wt_code, 'N/A',
                    len(wt_df),
                    wt_df['Conexiones_Internas'].mean() if 'Conexiones_Internas' in wt_df.columns else 0,
                    wt_df['Densidad_Segmento'].mean() if 'Densidad_Segmento' in wt_df.columns else 0,
                    wt_df['Centralidad_Grado_Promedio'].mean() if 'Centralidad_Grado_Promedio' in wt_df.columns else 0,
                    wt_df['Centralidad_Intermediacion_Promedio'].mean() if 'Centralidad_Intermediacion_Promedio' in wt_df.columns else 0
                ],
                'Reference': [
                    'N/A', 'hwt4_Hh2a_WT',
                    len(ref_df),
                    ref_df['Conexiones_Internas'].mean() if 'Conexiones_Internas' in ref_df.columns else 0,
                    ref_df['Densidad_Segmento'].mean() if 'Densidad_Segmento' in ref_df.columns else 0,
                    ref_df['Centralidad_Grado_Promedio'].mean() if 'Centralidad_Grado_Promedio' in ref_df.columns else 0,
                    ref_df['Centralidad_Intermediacion_Promedio'].mean() if 'Centralidad_Intermediacion_Promedio' in ref_df.columns else 0
                ]
            }
        else:
            # Para análisis por residuos, usar métricas tradicionales
            summary_data = {
                'Propiedad': [
                    'Toxina_WT', 'Toxina_Referencia',
                    'Numero_Residuos', 
                    'Centralidad_Grado_Promedio',
                    'Centralidad_Intermediacion_Promedio', 
                    'Centralidad_Cercania_Promedio',
                    'Coeficiente_Agrupamiento_Promedio'
                ],
                'WT_Target': [
                    wt_code, 'N/A',
                    len(wt_df),
                    wt_df['Centralidad_Grado'].mean() if 'Centralidad_Grado' in wt_df.columns else 0,
                    wt_df['Centralidad_Intermediacion'].mean() if 'Centralidad_Intermediacion' in wt_df.columns else 0,
                    wt_df['Centralidad_Cercania'].mean() if 'Centralidad_Cercania' in wt_df.columns else 0,
                    wt_df['Coeficiente_Agrupamiento'].mean() if 'Coeficiente_Agrupamiento' in wt_df.columns else 0
                ],
                'Reference': [
                    'N/A', 'hwt4_Hh2a_WT',
                    len(ref_df),
                    ref_df['Centralidad_Grado'].mean() if 'Centralidad_Grado' in ref_df.columns else 0,
                    ref_df['Centralidad_Intermediacion'].mean() if 'Centralidad_Intermediacion' in ref_df.columns else 0,
                    ref_df['Centralidad_Cercania'].mean() if 'Centralidad_Cercania' in ref_df.columns else 0,
                    ref_df['Coeficiente_Agrupamiento'].mean() if 'Coeficiente_Agrupamiento' in ref_df.columns else 0
                ]
            }
        
        return pd.DataFrame(summary_data)


class FamilyAnalysisProcessor:
    """Procesador para análisis de familias de toxinas."""
    
    @staticmethod
    def determine_family_wt(toxin_name: str, toxin_type: str) -> str:
        """
        Determina la familia WT de una toxina.
        
        Args:
            toxin_name: Nombre de la toxina
            toxin_type: Tipo de toxina
            
        Returns:
            Familia WT
        """
        if toxin_type == "WT_Target":
            if "μ-TRTX-Hh2a" in toxin_name:
                return "Mu-TRTX-2a"
            elif "μ-TRTX-Hhn2b" in toxin_name:
                return "Mu-TRTX-2b"
            elif "β-TRTX" in toxin_name:
                return "Beta-TRTX"
            elif "ω-TRTX" in toxin_name:
                return "Omega-TRTX"
            else:
                return "Unknown"
        else:
            return "Reference"
