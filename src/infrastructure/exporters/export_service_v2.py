from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import networkx as nx

from src.utils.excel_export import generate_excel


class ExportUtilsV2:
    @staticmethod
    def clean_filename(name: str, max_length: int = 31) -> str:
        import unicodedata, re
        normalized = unicodedata.normalize('NFKD', name)
        clean = (
            normalized
            .replace('μ', 'mu')
            .replace('β', 'beta')
            .replace('ω', 'omega')
            .replace('δ', 'delta')
        )
        clean = re.sub(r'[^\w\-_]', '', clean, flags=re.ASCII)
        return clean[:max_length] if clean else 'unknown'

    @staticmethod
    def normalize_ic50_to_nm(ic50_value: Optional[float], ic50_unit: Optional[str]) -> Optional[float]:
        try:
            from src.domain.models.value_objects import IC50
            return IC50.normalize_to_nm(ic50_value, ic50_unit)
        except Exception:
            return None if ic50_value is None else float(ic50_value)

    @staticmethod
    def family_filename_prefix(family_prefix: str, export_type: str, granularity: str) -> str:
        if family_prefix.startswith('μ-TRTX'):
            family_name = family_prefix.replace('μ', 'Mu', 1)
        elif family_prefix.startswith('β-TRTX'):
            family_name = family_prefix.replace('β', 'Beta', 1)
        elif family_prefix.startswith('ω-TRTX'):
            family_name = family_prefix.replace('ω', 'Omega', 1)
        else:
            mapping = {'μ': 'Mu-TRTX', 'β': 'Beta-TRTX', 'ω': 'Omega-TRTX'}
            family_name = mapping.get(family_prefix, family_prefix)

        if export_type == 'segments_atomicos':
            return f"Dataset_Familia_{family_name}_Segmentacion_Atomica_{granularity}"
        return f"Dataset_Familia_{family_name}_IC50_Topologia_{granularity}"

    @staticmethod
    def wt_filename_prefix(wt_family: str, export_type: str, granularity: str) -> str:
        clean = (
            wt_family.replace('μ', 'mu')
            .replace('β', 'beta')
            .replace('ω', 'omega')
            .replace('δ', 'delta')
        )
        if export_type == 'segments_atomicos':
            return f"Comparacion_WT_{clean}_vs_hwt4_Hh2a_WT_Segmentacion_Atomica_{granularity}"
        return f"Comparacion_WT_{clean}_vs_hwt4_Hh2a_WT_{granularity}"


class ExportService:
    @staticmethod
    def extract_residue_data(G, granularity: str) -> List[Dict[str, Any]]:
        degree_centrality = nx.degree_centrality(G) if G.number_of_nodes() else {}
        betweenness_centrality = nx.betweenness_centrality(G) if G.number_of_nodes() else {}
        closeness_centrality = nx.closeness_centrality(G) if G.number_of_nodes() else {}
        clustering_coefficient = nx.clustering(G) if G.number_of_nodes() else {}

        residue_data: List[Dict[str, Any]] = []
        for node in G.nodes():
            if granularity == 'CA':
                parts = str(node).split(':')
                if len(parts) >= 3:
                    chain = parts[0]
                    residue_name = parts[1]
                    residue_number = parts[2]
                else:
                    chain = G.nodes[node].get('chain_id', 'A')
                    residue_name = G.nodes[node].get('residue_name', 'UNK')
                    residue_number = str(node)
            else:
                chain = G.nodes[node].get('chain_id', 'A')
                residue_name = G.nodes[node].get('residue_name', 'UNK')
                residue_number = str(G.nodes[node].get('residue_number', node))

            residue_data.append({
                'Cadena': chain,
                'Residuo_Nombre': residue_name,
                'Residuo_Numero': residue_number,
                'Centralidad_Grado': round(degree_centrality.get(node, 0), 6) if degree_centrality else 0,
                'Centralidad_Intermediacion': round(betweenness_centrality.get(node, 0), 6) if betweenness_centrality else 0,
                'Centralidad_Cercania': round(closeness_centrality.get(node, 0), 6) if closeness_centrality else 0,
                'Coeficiente_Agrupamiento': round(clustering_coefficient.get(node, 0), 6) if clustering_coefficient else 0,
                'Grado_Nodo': G.degree(node)
            })
        return residue_data

    @staticmethod
    def prepare_residue_export_data(G, toxin_name: str, ic50_value: Optional[float] = None,
                                    ic50_unit: Optional[str] = None, granularity: str = 'CA') -> List[Dict[str, Any]]:
        rows = ExportService.extract_residue_data(G, granularity)
        for r in rows:
            r['Toxina'] = toxin_name
            if ic50_value is not None and ic50_unit:
                r['IC50_Value'] = ic50_value
                r['IC50_Unit'] = ic50_unit
                nm = ExportUtilsV2.normalize_ic50_to_nm(ic50_value, ic50_unit)
                if nm is not None:
                    r['IC50_nM'] = nm
        return rows

    @staticmethod
    def create_metadata(toxin_name: str, source: str, protein_id: int, granularity: str,
                        distance_threshold: float, long_threshold: int, G,
                        ic50_value: Optional[float] = None, ic50_unit: Optional[str] = None) -> Dict[str, Any]:
        meta: Dict[str, Any] = {
            'Toxina': toxin_name,
            'Fuente': source,
            'ID': protein_id,
            'Granularidad': granularity,
            'Umbral_Distancia': distance_threshold,
            'Umbral_Interaccion_Larga': long_threshold,
            'Densidad_del_grafo': round(nx.density(G), 6) if G.number_of_nodes() else 0,
            'Numero_de_nodos': G.number_of_nodes(),
            'Numero_de_aristas': G.number_of_edges(),
            'Fecha_Exportacion': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if ic50_value is not None and ic50_unit:
            meta['IC50_Original'] = ic50_value
            meta['Unidad_IC50'] = ic50_unit
            nm = ExportUtilsV2.normalize_ic50_to_nm(ic50_value, ic50_unit)
            if nm is not None:
                meta['IC50_nM'] = nm
        return meta

    @staticmethod
    def generate_single_toxin_excel(residue_data: List[Dict], metadata: Dict[str, Any],
                                    toxin_name: str, source: str) -> Tuple[bytes, str]:
        df = pd.DataFrame(residue_data)
        clean = ExportUtilsV2.clean_filename(toxin_name)
        prefix = f"Nav1.7-{clean}" if source == 'nav1_7' else f"Toxinas-{clean}"
        return generate_excel(df, prefix, metadata=metadata)

    @staticmethod
    def generate_family_excel(toxin_dataframes: Dict[str, pd.DataFrame], family_prefix: str,
                              metadata: Dict[str, Any], export_type: str = 'residues',
                              granularity: str = 'CA') -> Tuple[bytes, str]:
        prefix = ExportUtilsV2.family_filename_prefix(family_prefix, export_type, granularity)
        return generate_excel(toxin_dataframes, prefix, metadata=metadata)

    @staticmethod
    def generate_comparison_excel(comparison_dataframes: Dict[str, pd.DataFrame],
                                  wt_family: str, metadata: Dict[str, Any],
                                  export_type: str = 'residues', granularity: str = 'CA') -> Tuple[bytes, str]:
        prefix = ExportUtilsV2.wt_filename_prefix(wt_family, export_type, granularity)
        return generate_excel(comparison_dataframes, prefix, metadata=metadata)

    @staticmethod
    def create_summary_comparison_dataframe(wt_df: pd.DataFrame, ref_df: pd.DataFrame,
                                            wt_code: str, export_type: str = 'residues') -> pd.DataFrame:
        if export_type == 'segments_atomicos':
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
                    wt_df.get('Conexiones_Internas', pd.Series([0])).mean(),
                    wt_df.get('Densidad_Segmento', pd.Series([0])).mean(),
                    wt_df.get('Centralidad_Grado_Promedio', pd.Series([0])).mean(),
                    wt_df.get('Centralidad_Intermediacion_Promedio', pd.Series([0])).mean(),
                ],
                'Reference': [
                    'N/A', 'hwt4_Hh2a_WT',
                    len(ref_df),
                    ref_df.get('Conexiones_Internas', pd.Series([0])).mean(),
                    ref_df.get('Densidad_Segmento', pd.Series([0])).mean(),
                    ref_df.get('Centralidad_Grado_Promedio', pd.Series([0])).mean(),
                    ref_df.get('Centralidad_Intermediacion_Promedio', pd.Series([0])).mean(),
                ]
            }
        else:
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
                    wt_df.get('Centralidad_Grado', pd.Series([0])).mean(),
                    wt_df.get('Centralidad_Intermediacion', pd.Series([0])).mean(),
                    wt_df.get('Centralidad_Cercania', pd.Series([0])).mean(),
                    wt_df.get('Coeficiente_Agrupamiento', pd.Series([0])).mean(),
                ],
                'Reference': [
                    'N/A', 'hwt4_Hh2a_WT',
                    len(ref_df),
                    ref_df.get('Centralidad_Grado', pd.Series([0])).mean(),
                    ref_df.get('Centralidad_Intermediacion', pd.Series([0])).mean(),
                    ref_df.get('Centralidad_Cercania', pd.Series([0])).mean(),
                    ref_df.get('Coeficiente_Agrupamiento', pd.Series([0])).mean(),
                ]
            }
        return pd.DataFrame(summary_data)
