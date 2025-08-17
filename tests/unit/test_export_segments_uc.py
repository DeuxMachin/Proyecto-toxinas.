import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.application.use_cases.export_atomic_segments import ExportAtomicSegments, ExportAtomicSegmentsInput
import networkx as nx

class DummyStructures:
    def get_pdb(self, source, pid):
        return b"ATOM..."
    def get_psf(self, source, pid):
        return None

class DummyMetadata:
    def get_complete_toxin_data(self, source, pid):
        return {"pdb_data": b"ATOM...", "name": f"Nav1.7_{pid}", "ic50_value": None, "ic50_unit": None}

class DummyPDB:
    def prepare_temp_pdb(self, pdb_bytes: bytes) -> str:
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=".pdb")
        os.close(fd)
        with open(path, 'wb') as f:
            f.write(pdb_bytes or b"ATOM\n")
        return path

class DummyTmp:
    def cleanup(self, paths):
        for p in paths:
            try:
                import os
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

class DummyExporter:
    def generate_atomic_segments_excel(self, df_segments, toxin_name, metadata):
        # mimic return signature
        return b"bytes", f"Nav1.7-{toxin_name}-Segmentos-Atomicos.xlsx"

# Patch segmentation to return a tiny DataFrame

def test_export_atomic_segments_uc(monkeypatch):
    from src.application.use_cases import export_atomic_segments as mod
    import pandas as pd

    def fake_cfg(granularity, long, dist):
        return object()
    def fake_construct(path, cfg):
        G = nx.Graph()
        G.add_nodes_from([1,2,3])
        G.add_edges_from([(1,2),(2,3)])
        return G
    def fake_segment(G, granularity):
        return pd.DataFrame([{"Num_Atomos": 2, "Conexiones_Internas": 1, "Densidad_Segmento": 0.5}])

    # Patch GraphAnalyzer & segmentation
    from app.services import graph_analyzer as ga_mod
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "create_graph_config", staticmethod(fake_cfg))
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "construct_protein_graph", staticmethod(fake_construct))
    monkeypatch.setattr(mod, 'agrupar_por_segmentos_atomicos', fake_segment)

    uc = ExportAtomicSegments(DummyStructures(), DummyMetadata(), DummyPDB(), DummyTmp(), DummyExporter())
    content, filename, meta = uc.execute(ExportAtomicSegmentsInput(pid=1, granularity='atom'))

    assert isinstance(content, (bytes, bytearray))
    assert filename.startswith("Nav1.7-Nav1.7_1-Segmentos-Atomicos")
    assert meta["Tipo_Analisis"] == "Segmentación Atómica"
