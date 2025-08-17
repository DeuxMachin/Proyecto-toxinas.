import io
from typing import Dict, Any

class FakeExcelAdapter:
    def __init__(self):
        self.calls = []
    def generate_single_toxin_excel(self, residue_data, metadata: Dict[str, Any], toxin_name: str, source: str):
        self.calls.append(("single", toxin_name, source, metadata))
        return b"fake-bytes", f"{toxin_name}_{source}.xlsx"
    def generate_family_excel(self, toxin_dataframes, family_prefix: str, metadata: Dict[str, Any], export_type: str = 'residues', granularity: str = 'CA'):
        self.calls.append(("family", family_prefix, export_type, granularity))
        return b"fake-bytes", f"{family_prefix}_{export_type}.xlsx"
    def generate_comparison_excel(self, comparison_dataframes, wt_family: str, metadata: Dict[str, Any], export_type: str = 'residues', granularity: str = 'CA'):
        self.calls.append(("comparison", wt_family, export_type, granularity))
        return b"fake-bytes", f"comparison_{wt_family}_{export_type}.xlsx"


def test_single_toxin_excel_contract():
    adapter = FakeExcelAdapter()
    data = [{"residue": 1, "value": 0.5}]
    meta = {"granularity": "CA"}
    content, filename = adapter.generate_single_toxin_excel(data, meta, "ToxinA", "toxinas")
    assert isinstance(content, (bytes, bytearray))
    assert filename == "ToxinA_toxinas.xlsx"


def test_family_excel_contract():
    adapter = FakeExcelAdapter()
    dataframes = {"ToxinA": object()}
    meta = {"granularity": "CA"}
    content, filename = adapter.generate_family_excel(dataframes, "FamilyX", meta, export_type='segments', granularity='CB')
    assert isinstance(content, (bytes, bytearray))
    assert filename == "FamilyX_segments.xlsx"


def test_comparison_excel_contract():
    adapter = FakeExcelAdapter()
    dataframes = {"WT": object(), "Mut": object()}
    meta = {"granularity": "CA"}
    content, filename = adapter.generate_comparison_excel(dataframes, "WTFamily", meta, export_type='residues', granularity='CA')
    assert isinstance(content, (bytes, bytearray))
    assert filename == "comparison_WTFamily_residues.xlsx"
