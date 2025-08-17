from typing import Dict, List, Any, Tuple
from src.infrastructure.exporters.export_service_v2 import ExportService
from src.utils.excel_export import generate_excel


class ExportUtils:
    @staticmethod
    def clean_filename(name: str, max_length: int = 31) -> str:
        import unicodedata, re
        normalized = unicodedata.normalize('NFKD', name)
        clean = (normalized.replace('μ', 'mu').replace('β', 'beta').replace('ω', 'omega').replace('δ', 'delta'))
        clean = re.sub(r'[^\w\-_]', '', clean, flags=re.ASCII)
        return clean[:max_length] if clean else 'unknown'

class ExcelExportAdapter:
    def generate_single_toxin_excel(self, residue_data: List[Dict], metadata: Dict[str, Any], toxin_name: str, source: str) -> Tuple[bytes, str]:
        return ExportService.generate_single_toxin_excel(residue_data, metadata, toxin_name, source)

    def generate_family_excel(self, toxin_dataframes: Dict[str, Any], family_prefix: str, metadata: Dict[str, Any], export_type: str = 'residues', granularity: str = 'CA') -> Tuple[bytes, str]:
        return ExportService.generate_family_excel(toxin_dataframes, family_prefix, metadata, export_type, granularity)

    def generate_comparison_excel(self, comparison_dataframes: Dict[str, Any], wt_family: str, metadata: Dict[str, Any], export_type: str = 'residues', granularity: str = 'CA') -> Tuple[bytes, str]:
        return ExportService.generate_comparison_excel(comparison_dataframes, wt_family, metadata, export_type, granularity)

    def generate_atomic_segments_excel(self, df_segments: Any, toxin_name: str, metadata: Dict[str, Any]) -> Tuple[bytes, str]:
        """Generate Excel for atomic segments analysis of a single Nav1.7 toxin.

        Matches legacy filename pattern: "Nav1.7-{CleanName}-Segmentos-Atomicos_<timestamp>.xlsx"
        """
        clean = ExportUtils.clean_filename(toxin_name)
        filename_prefix = f"Nav1.7-{clean}-Segmentos-Atomicos"
        return generate_excel(df_segments, filename_prefix, metadata=metadata)
