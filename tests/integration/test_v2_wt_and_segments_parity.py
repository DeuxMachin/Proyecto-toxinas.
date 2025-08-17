import pandas as pd
from io import BytesIO


def test_wt_comparison_residues_columns_parity(monkeypatch, tmp_path):
    from src.interfaces.http.flask.app import create_app_v2
    app = create_app_v2()
    from src.application.use_cases import export_wt_comparison as mod
    from src.interfaces.http.flask.controllers.v2 import export_controller as ctl
    from src.infrastructure.exporters.excel_export_adapter import ExcelExportAdapter

    # Patch GraphAnalyzer to avoid heavy compute
    monkeypatch.setattr(mod.GraphAnalyzer, 'create_graph_config', lambda g, l, d: {})
    import networkx as nx
    monkeypatch.setattr(mod.GraphAnalyzer, 'construct_protein_graph', lambda path, cfg: nx.Graph())

    # Patch ExportService rows with expected residue columns
    class _ES:
        @staticmethod
        def prepare_residue_export_data(G, toxin_name, ic50_value, ic50_unit, granularity):
            return [{
                'Cadena': 'A', 'Residuo_Nombre': 'VAL', 'Residuo_Numero': '21',
                'Centralidad_Grado': 0.1, 'Centralidad_Intermediacion': 0.2,
                'Centralidad_Cercania': 0.3, 'Coeficiente_Agrupamiento': 0.4,
                'Grado_Nodo': 5, 'Toxina': toxin_name
            }]
    monkeypatch.setattr(mod, 'ExportService', _ES)

    # Fake repos and UC wiring
    class FakeMeta:
        def get_wt_toxin_data(self, code):
            return {'id': 1, 'name': 'μ-TRTX-Hh2a', 'ic50_value': 12.3, 'ic50_unit': 'nM', 'pdb_data': b'ATOM X'}
    class FakeStruct:
        pass

    # Build a new UC instance and inject into controller
    uc = mod.ExportWTComparison(FakeMeta(), FakeStruct(), ExcelExportAdapter())
    ctl.configure_export_dependencies(wt_uc=uc)

    # Reference PDB file
    ref = tmp_path / 'ref.pdb'
    ref.write_text('ATOM REF')

    with app.test_client() as c:
        # mu encoded in URL to ensure routing works with unicode
        r = c.get(f"/v2/export/wt_comparison/%CE%BC-TRTX-Hh2a?export_type=residues&granularity=CA&reference_path={ref}")
        assert r.status_code == 200
        assert r.mimetype.endswith('spreadsheetml.sheet')
        xls = pd.ExcelFile(BytesIO(r.data))
        assert 'Metadatos' in xls.sheet_names
        # Expect WT_Target and Reference sheets present
        assert 'WT_Target' in xls.sheet_names and 'Reference' in xls.sheet_names
        df = pd.read_excel(xls, sheet_name='WT_Target')
        expected = {'Cadena','Residuo_Nombre','Residuo_Numero','Centralidad_Grado','Centralidad_Intermediacion','Centralidad_Cercania','Coeficiente_Agrupamiento','Grado_Nodo','Toxina','Tipo'}
        assert expected.issubset(set(df.columns))


def test_wt_comparison_segments_columns_parity(monkeypatch, tmp_path):
    from src.interfaces.http.flask.app import create_app_v2
    app = create_app_v2()
    from src.application.use_cases import export_wt_comparison as mod
    from src.interfaces.http.flask.controllers.v2 import export_controller as ctl
    from src.infrastructure.exporters.excel_export_adapter import ExcelExportAdapter

    # Patch GraphAnalyzer and segmentation
    monkeypatch.setattr(mod.GraphAnalyzer, 'create_graph_config', lambda g, l, d: {})
    import networkx as nx
    monkeypatch.setattr(mod.GraphAnalyzer, 'construct_protein_graph', lambda path, cfg: nx.Graph())

    def fake_segment(G, granularity):
        return pd.DataFrame([{
            'Segmento_ID': 'RES_021', 'Num_Atomos': 3, 'Conexiones_Internas': 2,
            'Densidad_Segmento': 0.5,
            'Centralidad_Grado_Promedio': 0.1,
            'Centralidad_Intermediacion_Promedio': 0.2,
            'Centralidad_Cercania_Promedio': 0.3,
            'Coeficiente_Agrupamiento_Promedio': 0.4,
            'Residuo_Nombre': 'VAL', 'Residuo_Numero': 21, 'Cadena': 'A'
        }])
    monkeypatch.setattr(mod, 'agrupar_por_segmentos_atomicos', fake_segment)

    class FakeMeta:
        def get_wt_toxin_data(self, code):
            return {'id': 1, 'name': 'μ-TRTX-Hh2a', 'ic50_value': 12.3, 'ic50_unit': 'nM', 'pdb_data': b'ATOM X'}
    class FakeStruct:
        pass

    uc = mod.ExportWTComparison(FakeMeta(), FakeStruct(), ExcelExportAdapter())
    ctl.configure_export_dependencies(wt_uc=uc)

    ref = tmp_path / 'ref.pdb'
    ref.write_text('ATOM REF')

    with app.test_client() as c:
        r = c.get(f"/v2/export/wt_comparison/%CE%BC-TRTX-Hh2a?export_type=segments_atomicos&granularity=atom&reference_path={ref}")
        assert r.status_code == 200
        assert r.mimetype.endswith('spreadsheetml.sheet')
        xls = pd.ExcelFile(BytesIO(r.data))
        assert 'Metadatos' in xls.sheet_names
        assert 'WT_Target' in xls.sheet_names and 'Reference' in xls.sheet_names
        df = pd.read_excel(xls, sheet_name='WT_Target')
    expected = {'Segmento_ID','Num_Atomos','Conexiones_Internas','Densidad_Segmento','Centralidad_Grado_Promedio','Centralidad_Intermediacion_Promedio','Centralidad_Cercania_Promedio','Coeficiente_Agrupamiento_Promedio','Residuo_Nombre','Residuo_Numero','Cadena','Toxina','Tipo','IC50_Value','IC50_Unit'}
    assert expected.issubset(set(df.columns))


def test_atomic_segments_uc_uses_domain_segmentation(monkeypatch):
    from src.interfaces.http.flask.app import create_app_v2
    app = create_app_v2()
    from src.application.use_cases import export_atomic_segments as mod
    from src.interfaces.http.flask.controllers.v2 import export_controller as ctl

    # Stub _graph_api to return a simple GraphAnalyzer with trivial methods
    import networkx as nx
    class _StubGA:
        @staticmethod
        def create_graph_config(g, l, d):
            return {}
        @staticmethod
        def construct_protein_graph(path, cfg):
            G = nx.Graph()
            G.add_node('A:VAL:1:CA', chain='A', residue='VAL', resnum=1)
            return G

    monkeypatch.setattr(mod, '_graph_api', lambda: type('_GA', (), {'GraphAnalyzer': _StubGA}))

    # Patch the module-level agrupar_por_segmentos_atomicos to return a sentinel column
    def fake_seg(G, gran):
        return pd.DataFrame([{'Num_Atomos': 1, 'Conexiones_Internas': 0, 'Densidad_Segmento': 0.0,
                              'Centralidad_Grado_Promedio': 0.0, 'Centralidad_Intermediacion_Promedio': 0.0,
                              'Centralidad_Cercania_Promedio': 0.0, 'Coeficiente_Agrupamiento_Promedio': 0.0,
                              'Residuo_Nombre': 'UNK', 'Residuo_Numero': 1, 'Cadena': 'A', 'SENTINEL': 'ok'}])
    monkeypatch.setattr(mod, 'agrupar_por_segmentos_atomicos', fake_seg)

    # Fake metadata to ensure a PDB is returned
    class FakeMeta:
        def get_complete_toxin_data(self, source, pid):
            return {'name': 'Nav1.7_X', 'pdb_data': b'ATOM X', 'ic50_value': None, 'ic50_unit': None}
    class FakeStruct: 
        pass

    # Rebuild segments UC with our fake metadata
    from src.infrastructure.exporters.excel_export_adapter import ExcelExportAdapter
    from src.infrastructure.pdb.pdb_preprocessor_adapter import PDBPreprocessorAdapter
    from src.infrastructure.fs.temp_file_service import TempFileService
    uc = mod.ExportAtomicSegments(FakeStruct(), FakeMeta(), PDBPreprocessorAdapter(), TempFileService(), ExcelExportAdapter())
    ctl.configure_export_dependencies(segments_uc=uc)

    with app.test_client() as c:
        r = c.get('/v2/export/segments_atomicos/1?granularity=atom')
        assert r.status_code == 200
        xls = pd.ExcelFile(BytesIO(r.data))
        data_sheet = next(sn for sn in xls.sheet_names if sn != 'Metadatos')
        df = pd.read_excel(xls, sheet_name=data_sheet)
        assert 'SENTINEL' in df.columns


def test_wt_comparison_resumen_sheet_and_ic50_residues(monkeypatch, tmp_path):
    """Ensure summary sheet is present and IC50 columns are included using real ExportService."""
    from src.interfaces.http.flask.app import create_app_v2
    app = create_app_v2()
    from src.application.use_cases import export_wt_comparison as mod
    from src.interfaces.http.flask.controllers.v2 import export_controller as ctl
    from src.infrastructure.exporters.excel_export_adapter import ExcelExportAdapter

    # Patch GraphAnalyzer to return a tiny non-empty graph
    import networkx as nx
    class _StubGA:
        @staticmethod
        def create_graph_config(g, l, d):
            return {}
        @staticmethod
        def construct_protein_graph(path, cfg):
            G = nx.Graph()
            G.add_node('A:VAL:1:CA', chain_id='A', residue_name='VAL', residue_number=1)
            return G
    monkeypatch.setattr(mod, 'GraphAnalyzer', _StubGA)

    # Use real ExportService from app.services for IC50 + summary
    class FakeMeta:
        def get_wt_toxin_data(self, code):
            return {'id': 1, 'name': 'μ-TRTX-Hh2a', 'ic50_value': 12.3, 'ic50_unit': 'nM', 'pdb_data': b'ATOM X'}
    class FakeStruct: pass
    uc = mod.ExportWTComparison(FakeMeta(), FakeStruct(), ExcelExportAdapter())
    ctl.configure_export_dependencies(wt_uc=uc)

    ref = tmp_path / 'ref.pdb'
    ref.write_text('ATOM REF')

    with app.test_client() as c:
        r = c.get(f"/v2/export/wt_comparison/%CE%BC-TRTX-Hh2a?export_type=residues&granularity=CA&reference_path={ref}")
        assert r.status_code == 200
        xls = pd.ExcelFile(BytesIO(r.data))
        # Summary sheet present if service supports it
        assert 'Resumen_Comparativo' in xls.sheet_names
        df_wt = pd.read_excel(xls, sheet_name='WT_Target')
        # IC50 fields should be present in residues export when ic50 present
        assert {'IC50_Value','IC50_Unit','IC50_nM'}.issubset(set(df_wt.columns))


def test_v2_export_residues_ignores_legacy_pdb_processor(monkeypatch):
    """If legacy PDBProcessor were called, raise; v2 must still work using its own adapter."""
    from src.interfaces.http.flask.app import create_app_v2
    app = create_app_v2()
    from src.interfaces.http.flask.controllers.v2 import export_controller as ctl
    from src.application.use_cases import export_residue_report as uc_mod

    # Make legacy PDBProcessor fail if ever called
    import app.services.pdb_processor as legacy_pp
    def boom(*a, **k):
        raise RuntimeError('legacy PDBProcessor should not be used in v2')
    monkeypatch.setattr(legacy_pp.PDBProcessor, 'create_temp_pdb_file', boom)

    # Stub GraphAnalyzer to avoid heavy compute
    class _StubGA:
        @staticmethod
        def create_graph_config(g, l, d):
            return {}
        @staticmethod
        def construct_protein_graph(path, cfg):
            import networkx as nx
            G = nx.Graph()
            G.add_node('A:VAL:1:CA', chain_id='A', residue_name='VAL', residue_number=1)
            return G
    monkeypatch.setattr(uc_mod, 'GraphAnalyzer', _StubGA)

    # Fake repos and inject a fresh UC using v2 adapters
    class FakeMeta:
        def get_complete_toxin_data(self, source, pid):
            return {'name': 'Nav1.7_X', 'pdb_data': b'ATOM X', 'ic50_value': 1.0, 'ic50_unit': 'nM'}
    class FakeStruct: pass
    from src.infrastructure.exporters.excel_export_adapter import ExcelExportAdapter
    from src.infrastructure.pdb.pdb_preprocessor_adapter import PDBPreprocessorAdapter
    from src.infrastructure.fs.temp_file_service import TempFileService
    uc = uc_mod.ExportResidueReport(FakeStruct(), ExcelExportAdapter(), PDBPreprocessorAdapter(), TempFileService(), FakeMeta())
    ctl.configure_export_dependencies(export_uc=uc)

    with app.test_client() as c:
        r = c.get('/v2/export/residues/nav1_7/1?granularity=CA')
        assert r.status_code == 200


def test_v2_dipole_ignores_legacy_pdb_processor(monkeypatch):
    from src.interfaces.http.flask.app import create_app_v2
    app = create_app_v2()
    from src.interfaces.http.flask.controllers.v2 import dipole_controller as dctl
    from src.application.use_cases.calculate_dipole import CalculateDipole, CalculateDipoleInput

    # Force legacy PDBProcessor to fail if touched
    import app.services.pdb_processor as legacy_pp
    monkeypatch.setattr(legacy_pp.PDBProcessor, 'create_temp_pdb_file', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('legacy used')))

    # Stub CalculateDipole to bypass heavy compute and file use
    class FakeUseCase(CalculateDipole):
        def __init__(self):
            pass
        def execute(self, inp: CalculateDipoleInput):
            return {"success": True, "dipole": {"magnitude": 1.23, "direction": [0,0,1]}}

    # Inject stubbed UC
    dctl.configure_dipole_dependencies(use_case=FakeUseCase())

    with app.test_client() as c:
        r = c.post('/v2/dipole/nav1_7/1')
        assert r.status_code == 200
