import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.application.use_cases.export_wt_comparison import ExportWTComparison, ExportWTComparisonInput
import networkx as nx

class DummyMetadata:
    def get_wt_toxin_data(self, peptide_code):
        return {"pdb_data": b"ATOM...", "name": peptide_code, "ic50_value": 1.2, "ic50_unit": "nM"}

class DummyStructures:
    def get_pdb(self, source, pid):
        return b"ATOM..."

class DummyExporter:
    def generate_comparison_excel(self, comparison_frames, wt_family, meta, export_type='residues', granularity='CA'):
        assert isinstance(comparison_frames, dict) and comparison_frames
        return b"bytes", f"Comparacion_WT_{wt_family}_vs_hwt4_Hh2a_WT_{granularity}.xlsx"

class DummyPDBFile:
    @staticmethod
    def create(path):
        import tempfile
        with open(path, 'w') as f:
            f.write("ATOM\n")

# Patch GA, segmentation, file IO

def test_export_wt_comparison_uc_residues(monkeypatch, tmp_path):
    from src.application.use_cases import export_wt_comparison as mod
    import pandas as pd

    def fake_cfg(granularity, long, dist):
        return object()
    def fake_construct(path, cfg):
        G = nx.Graph()
        G.add_nodes_from([1,2,3,4,5])
        G.add_edges_from([(1,2),(2,3),(3,4),(4,5),(5,1),(1,3),(2,4)])
        return G
    def fake_prepare(G, name, ic50_value, ic50_unit, granularity):
        return [{"Toxina": name, "Centralidad_Grado": 0.1}]

    from app.services import graph_analyzer as ga_mod
    from app.services import export_service as ex_mod

    monkeypatch.setattr(ga_mod.GraphAnalyzer, "create_graph_config", staticmethod(fake_cfg))
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "construct_protein_graph", staticmethod(fake_construct))
    monkeypatch.setattr(ex_mod.ExportService, "prepare_residue_export_data", staticmethod(fake_prepare))

    # create reference file
    ref = tmp_path / 'ref.pdb'
    ref.write_text('ATOM\n')

    uc = ExportWTComparison(DummyMetadata(), DummyStructures(), DummyExporter())
    inp = ExportWTComparisonInput(wt_family='μ-TRTX-Hh2a', export_type='residues', granularity='CA', reference_path=str(ref))
    content, filename, meta = uc.execute(inp)

    assert isinstance(content, (bytes, bytearray))
    assert filename.startswith("Comparacion_WT_")
    assert meta["Familia"] == 'μ-TRTX-Hh2a'


def test_export_wt_comparison_uc_segments(monkeypatch, tmp_path):
    from src.application.use_cases import export_wt_comparison as mod
    import pandas as pd

    def fake_cfg(granularity, long, dist):
        return object()
    def fake_construct(path, cfg):
        G = nx.Graph()
        G.add_nodes_from([1,2,3,4,5])
        G.add_edges_from([(1,2),(2,3),(3,4),(4,5),(5,1),(1,3),(2,4)])
        return G
    def fake_segment(G, granularity):
        import pandas as pd
        return pd.DataFrame([{"Num_Atomos": 2, "Conexiones_Internas": 1, "Densidad_Segmento": 0.5}])
    def fake_segment(G, granularity):
        return pd.DataFrame([{"Num_Atomos": 2}])

    from app.services import graph_analyzer as ga_mod
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "create_graph_config", staticmethod(fake_cfg))
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "construct_protein_graph", staticmethod(fake_construct))

    ref = tmp_path / 'ref2.pdb'
    ref.write_text('ATOM\n')

    # Patch segmentation
    monkeypatch.setattr(mod, 'agrupar_por_segmentos_atomicos', fake_segment)
    uc = ExportWTComparison(DummyMetadata(), DummyStructures(), DummyExporter())
    inp = ExportWTComparisonInput(wt_family='μ-TRTX-Hh2a', export_type='segments_atomicos', granularity='atom', reference_path=str(ref))
    content, filename, meta = uc.execute(inp)

    assert isinstance(content, (bytes, bytearray))
    assert filename.startswith("Comparacion_WT_")
    assert meta["Tipo_Analisis"].startswith("Segmentación")
