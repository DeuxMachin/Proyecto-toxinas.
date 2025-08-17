import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.application.use_cases.export_family_reports import ExportFamilyReports, ExportFamilyInput
import networkx as nx

class DummyMetadata:
    def get_family_toxins(self, family_prefix):
        # Return two items: (id, code, ic50_value, ic50_unit)
        return [
            (1, f"{family_prefix}", 12.3, "nM"),
            (2, f"{family_prefix}_Mut", None, None),
        ]

class DummyStructures:
    def get_pdb(self, source, pid):
        return b"ATOM..."

class DummyExporter:
    def generate_family_excel(self, toxin_dataframes, family_prefix, metadata, export_type='residues', granularity='CA'):
        # Filename parity with ExportService.generate_family_excel is tested indirectly in adapter tests.
        assert isinstance(toxin_dataframes, dict) and toxin_dataframes
        assert metadata.get('Familia') == family_prefix
        if export_type == 'segments_atomicos':
            return b"bytes", f"Dataset_Familia_{family_prefix}_Segmentacion_Atomica_{granularity}.xlsx"
        return b"bytes", f"Dataset_Familia_{family_prefix}_IC50_Topologia_{granularity}.xlsx"

# Patch GA & helpers to avoid heavy compute

def test_export_family_residues_uc(monkeypatch):
    from src.application.use_cases import export_family_reports as mod
    import pandas as pd

    def fake_cfg(granularity, long, dist):
        return object()
    def fake_construct(path, cfg):
        G = nx.Graph()
        G.add_nodes_from([1,2,3,4])
        G.add_edges_from([(1,2),(2,3),(3,4),(4,1),(1,3)])
        return G
    def fake_prepare(G, name, ic50_value, ic50_unit, granularity):
        return [{"Toxina": name, "Centralidad_Grado": 0.1}]

    from app.services import graph_analyzer as ga_mod
    from app.services import export_service as ex_mod
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "create_graph_config", staticmethod(fake_cfg))
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "construct_protein_graph", staticmethod(fake_construct))
    monkeypatch.setattr(ex_mod.ExportService, "prepare_residue_export_data", staticmethod(fake_prepare))

    uc = ExportFamilyReports(DummyMetadata(), DummyStructures(), DummyExporter())
    content, filename, meta = uc.execute(ExportFamilyInput(family_prefix='μ-TRTX-Hh2a', export_type='residues', granularity='CA'))

    assert isinstance(content, (bytes, bytearray))
    assert filename.startswith("Dataset_Familia_Mu-TRTX-Hh2a_IC50_Topologia_CA") or filename.startswith("Dataset_Familia_μ-TRTX-Hh2a_IC50_Topologia_CA")
    assert meta["Familia"] == 'μ-TRTX-Hh2a'


def test_export_family_segments_uc(monkeypatch):
    from src.application.use_cases import export_family_reports as mod
    import pandas as pd

    def fake_cfg(granularity, long, dist):
        return object()
    def fake_construct(path, cfg):
        G = nx.Graph()
        G.add_nodes_from([1,2,3,4])
        G.add_edges_from([(1,2),(2,3),(3,4),(4,1),(1,3)])
        return G
    def fake_segment(G, granularity):
        return pd.DataFrame([{"Num_Atomos": 2}])

    from app.services import graph_analyzer as ga_mod
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "create_graph_config", staticmethod(fake_cfg))
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "construct_protein_graph", staticmethod(fake_construct))
    monkeypatch.setattr(mod, 'agrupar_por_segmentos_atomicos', fake_segment)

    uc = ExportFamilyReports(DummyMetadata(), DummyStructures(), DummyExporter())
    content, filename, meta = uc.execute(ExportFamilyInput(family_prefix='β-TRTX', export_type='segments_atomicos', granularity='atom'))

    assert isinstance(content, (bytes, bytearray))
    assert filename.startswith("Dataset_Familia_Beta-TRTX_Segmentacion_Atomica_atom") or filename.startswith("Dataset_Familia_β-TRTX_Segmentacion_Atomica_atom")
    assert meta["Familia"] == 'β-TRTX'
