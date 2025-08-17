from io import BytesIO


class StubExportUC:
    def __init__(self, payload=None):
        self.payload = payload or ({'meta': True}, 'file.xlsx', {'ok': True})

    def execute(self, inp):
        # Return BytesIO, filename, metadata
        return BytesIO(b"excel"), 'demo.xlsx', {'ok': True, 'args': getattr(inp, '__dict__', {})}


class StubDipoleUC:
    def execute(self, inp):
        return {"success": True, "dipole": [1.0, 2.0, 3.0], "magnitude": 3.74}


def test_v2_export_residues_json(monkeypatch):
    from app import create_app
    # Monkeypatch controllers' use case singletons
    import src.interfaces.http.flask.controllers.v2.export_controller as exp_mod
    exp_mod._export_uc = StubExportUC()

    app = create_app()
    client = app.test_client()
    res = client.get('/v2/export/residues/nav1_7/123?format=json')
    assert res.status_code == 200
    data = res.get_json()
    # Presenter returns nested envelope: { meta: {...}, file: { filename, size_bytes, content_type } }
    assert 'file' in data and 'meta' in data
    assert data['file']['filename'].endswith('.xlsx')


def test_v2_export_segments_json(monkeypatch):
    from app import create_app
    import src.interfaces.http.flask.controllers.v2.export_controller as exp_mod
    exp_mod._segments_uc = StubExportUC()

    app = create_app()
    client = app.test_client()
    res = client.get('/v2/export/segments_atomicos/456?granularity=atom&format=json')
    assert res.status_code == 200
    data = res.get_json()
    assert data['file']['filename'].endswith('.xlsx')


def test_v2_export_family_json(monkeypatch):
    from app import create_app
    import src.interfaces.http.flask.controllers.v2.export_controller as exp_mod
    exp_mod._family_uc = StubExportUC()

    app = create_app()
    client = app.test_client()
    res = client.get('/v2/export/family/mu-TRTX?format=json')
    assert res.status_code == 200
    data = res.get_json()
    assert 'file' in data and data['file']['filename'].endswith('.xlsx')


def test_v2_export_wt_comparison_json(monkeypatch):
    from app import create_app
    import src.interfaces.http.flask.controllers.v2.export_controller as exp_mod
    exp_mod._wt_uc = StubExportUC()

    app = create_app()
    client = app.test_client()
    res = client.get('/v2/export/wt_comparison/μ-TRTX-Hh2a?format=json')
    assert res.status_code == 200
    data = res.get_json()
    assert 'meta' in data and 'file' in data


def test_v2_dipole_json(monkeypatch):
    from app import create_app
    import src.interfaces.http.flask.controllers.v2.dipole_controller as dip_mod
    dip_mod._dipole_uc = StubDipoleUC()

    app = create_app()
    client = app.test_client()
    res = client.post('/v2/dipole/nav1_7/99')
    assert res.status_code == 200
    data = res.get_json()
    assert 'result' in data and data['result']['success'] is True and 'dipole' in data['result']

    def test_v2_export_residues_excel(monkeypatch):
        from app import create_app
        import src.interfaces.http.flask.controllers.v2.export_controller as exp_mod
        exp_mod._export_uc = StubExportUC()

        app = create_app()
        client = app.test_client()
        res = client.get('/v2/export/residues/nav1_7/123')
        assert res.status_code == 200
        assert res.headers.get('Content-Type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        disp = res.headers.get('Content-Disposition', '')
        assert 'attachment' in disp and 'demo.xlsx' in disp

    def test_v2_export_segments_excel(monkeypatch):
        from app import create_app
        import src.interfaces.http.flask.controllers.v2.export_controller as exp_mod
        exp_mod._segments_uc = StubExportUC()

        app = create_app()
        client = app.test_client()
        res = client.get('/v2/export/segments_atomicos/456?granularity=atom')
        assert res.status_code == 200
        assert res.headers.get('Content-Type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def test_v2_export_family_excel(monkeypatch):
        from app import create_app
        import src.interfaces.http.flask.controllers.v2.export_controller as exp_mod
        exp_mod._family_uc = StubExportUC()

        app = create_app()
        client = app.test_client()
        res = client.get('/v2/export/family/mu-TRTX')
        assert res.status_code == 200
        assert res.headers.get('Content-Type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def test_v2_export_wt_comparison_excel(monkeypatch):
        from app import create_app
        import src.interfaces.http.flask.controllers.v2.export_controller as exp_mod
        exp_mod._wt_uc = StubExportUC()

        app = create_app()
        client = app.test_client()
        res = client.get('/v2/export/wt_comparison/μ-TRTX-Hh2a')
        assert res.status_code == 200
        assert res.headers.get('Content-Type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
