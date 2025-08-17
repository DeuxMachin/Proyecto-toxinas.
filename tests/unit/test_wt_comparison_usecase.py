import io
import pandas as pd
import networkx as nx


def make_stub_graph():
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2])
    G.add_edge(0, 1)
    G.add_edge(1, 2)
    return G


class StubMetadataRepo:
    def __init__(self, wt_record):
        self._wt = wt_record

    def get_wt_toxin_data(self, peptide_code):
        return self._wt


class StubStructureRepo:
    pass


class StubExcelExporter:
    def generate_comparison_excel(self, comparison_dataframes, wt_family, metadata, export_type='residues', granularity='CA'):
        return io.BytesIO(b"excel-bytes"), f"Comparacion_{wt_family}_{export_type}_{granularity}.xlsx"


def test_wt_comparison_residues(monkeypatch, tmp_path):
    from src.application.use_cases import export_wt_comparison as mod

    # Monkeypatch GraphAnalyzer
    monkeypatch.setattr(mod.GraphAnalyzer, 'create_graph_config', lambda g, l, d: {'g': g, 'l': l, 'd': d})
    monkeypatch.setattr(mod.GraphAnalyzer, 'construct_protein_graph', lambda path, cfg: make_stub_graph())

    # Monkeypatch PDBProcessor and reference file
    ref = tmp_path / 'ref.pdb'
    ref.write_text('ATOM FAKE REF PDB')
    monkeypatch.setattr(mod.PDBProcessor, 'prepare_pdb_data', lambda pdb: pdb)
    monkeypatch.setattr(mod.PDBProcessor, 'create_temp_pdb_file', lambda content: '/tmp/fake.pdb')
    monkeypatch.setattr(mod.PDBProcessor, 'cleanup_temp_files', lambda path: None)

    # Monkeypatch ExportService.prepare_residue_export_data
    class _ES:
        @staticmethod
        def prepare_residue_export_data(G, toxin_name, ic50_value, ic50_unit, granularity):
            return [
                {'Centralidad_Grado': 0.1, 'Centralidad_Intermediacion': 0.2,
                 'Centralidad_Cercania': 0.3, 'Coeficiente_Agrupamiento': 0.4,
                 'Toxina': toxin_name}
            ]
    monkeypatch.setattr(mod, 'ExportService', _ES)

    metadata = StubMetadataRepo({
        'id': 1,
        'name': 'μ-TRTX-Hh2a',
        'ic50_value': 12.3,
        'ic50_unit': 'nM',
        'pdb_data': b'ATOM FAKE'
    })
    exporter = StubExcelExporter()
    uc = mod.ExportWTComparison(metadata, StubStructureRepo(), exporter)
    inp = mod.ExportWTComparisonInput(wt_family='μ-TRTX-Hh2a', export_type='residues', granularity='CA', reference_path=str(ref))

    excel_data, excel_filename, meta = uc.execute(inp)
    assert hasattr(excel_data, 'read')
    assert 'Comparacion_μ-TRTX-Hh2a_residues_CA' in excel_filename
    assert meta['Familia'] == 'μ-TRTX-Hh2a'


def test_wt_comparison_segments(monkeypatch, tmp_path):
    from src.application.use_cases import export_wt_comparison as mod

    # Monkeypatch GraphAnalyzer
    monkeypatch.setattr(mod.GraphAnalyzer, 'create_graph_config', lambda g, l, d: {'g': g, 'l': l, 'd': d})
    monkeypatch.setattr(mod.GraphAnalyzer, 'construct_protein_graph', lambda path, cfg: make_stub_graph())

    # Monkeypatch PDBProcessor and reference file
    ref = tmp_path / 'ref.pdb'
    ref.write_text('ATOM FAKE REF PDB')
    monkeypatch.setattr(mod.PDBProcessor, 'prepare_pdb_data', lambda pdb: pdb)
    monkeypatch.setattr(mod.PDBProcessor, 'create_temp_pdb_file', lambda content: '/tmp/fake.pdb')
    monkeypatch.setattr(mod.PDBProcessor, 'cleanup_temp_files', lambda path: None)

    # Monkeypatch atomic segmentation
    def fake_segment(G, granularity):
        return pd.DataFrame([
            {'Num_Atomos': 3, 'Conexiones_Internas': 2, 'Densidad_Segmento': 0.5,
             'Centralidad_Grado_Promedio': 0.1, 'Centralidad_Intermediacion_Promedio': 0.2,
             'Centralidad_Cercania_Promedio': 0.3, 'Coeficiente_Agrupamiento_Promedio': 0.4}
        ])
    monkeypatch.setattr(mod, 'agrupar_por_segmentos_atomicos', fake_segment)

    metadata = StubMetadataRepo({
        'id': 1,
        'name': 'μ-TRTX-Hh2a',
        'ic50_value': 12.3,
        'ic50_unit': 'nM',
        'pdb_data': b'ATOM FAKE'
    })
    exporter = StubExcelExporter()
    uc = mod.ExportWTComparison(metadata, StubStructureRepo(), exporter)
    inp = mod.ExportWTComparisonInput(wt_family='μ-TRTX-Hh2a', export_type='segments_atomicos', granularity='atom', reference_path=str(ref))

    excel_data, excel_filename, meta = uc.execute(inp)
    assert hasattr(excel_data, 'read')
    assert 'Comparacion_μ-TRTX-Hh2a_segments_atomicos_atom' in excel_filename
    assert meta['Tipo_Analisis'] == 'Segmentación Atómica'
