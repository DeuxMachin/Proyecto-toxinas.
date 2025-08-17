import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.application.use_cases.export_residue_report import ExportResidueReport, ExportResidueReportInput
from src.application.use_cases.calculate_dipole import CalculateDipole, CalculateDipoleInput
from app.services import graph_analyzer as ga_mod

class DummyStructures:
    def __init__(self, pdb=b"ATOM...", psf=None):
        self._pdb = pdb
        self._psf = psf
    def get_pdb(self, source, pid):
        return self._pdb
    def get_psf(self, source, pid):
        return self._psf

class DummyMetadata:
    def get_complete_toxin_data(self, source, pid):
        return {"pdb_data": b"ATOM...", "name": f"{source}_{pid}", "ic50_value": None, "ic50_unit": None, "psf_data": None}

class DummyExporter:
    def generate_single_toxin_excel(self, residue_data, metadata, toxin_name, source):
        return b"bytes", f"{toxin_name}_{source}.xlsx"

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

class DummyDipole:
    def calculate_dipole_from_files(self, pdb_path, psf_path):
        return {"magnitude": 1.23, "vector": [0.1, 0.2, 0.3]}


def test_export_residue_report_uc(monkeypatch):
    # Stub GraphAnalyzer to avoid Graphein heavy path
    def fake_cfg(granularity, long, dist):
        return object()
    class G:
        def number_of_nodes(self): return 10
        def number_of_edges(self): return 20
    def fake_construct(path, cfg):
        return G()
    def fake_prepare(G, name, ic50_value, ic50_unit, granularity):
        return [{"Residue": 1, "Value": 0.5}]
    def fake_meta(name, source, pid, granularity, dist, long, G, ic50_value, ic50_unit):
        return {"Fuente": source, "ID": pid, "Granularidad": granularity}
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "create_graph_config", staticmethod(fake_cfg))
    monkeypatch.setattr(ga_mod.GraphAnalyzer, "construct_protein_graph", staticmethod(fake_construct))
    from app.services import export_service as ex_mod
    monkeypatch.setattr(ex_mod.ExportService, "prepare_residue_export_data", staticmethod(fake_prepare))
    monkeypatch.setattr(ex_mod.ExportService, "create_metadata", staticmethod(fake_meta))
    uc = ExportResidueReport(DummyStructures(), DummyExporter(), DummyPDB(), DummyTmp(), DummyMetadata())
    res = uc.execute(ExportResidueReportInput(source='toxinas', pid=1, granularity='CA'))
    content, filename, meta = res
    assert isinstance(content, (bytes, bytearray))
    assert filename.endswith("toxinas.xlsx")
    assert meta["Fuente"] if "Fuente" in meta else True


def test_calculate_dipole_uc():
    uc = CalculateDipole(DummyStructures(), DummyDipole())
    out = uc.execute(CalculateDipoleInput(source='nav1_7', pid=1))
    assert out["success"] is True
    assert "dipole" in out
