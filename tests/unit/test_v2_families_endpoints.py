import json
import urllib.parse

from src.interfaces.http.flask.app import create_app_v2


def test_list_families_v2():
    app = create_app_v2()
    app.testing = True
    with app.test_client() as c:
        r = c.get('/v2/families')
        assert r.status_code == 200
        data = r.get_json()
        assert data and data.get('success') is True
        assert isinstance(data.get('families'), list)
        # Expect our curated set
        values = {f['value'] for f in data['families']}
        assert {'μ-TRTX-Hh2a', 'μ-TRTX-Hhn2b', 'β-TRTX', 'ω-TRTX-Gr2a'} <= values


def test_family_peptides_original_plus_modified_v2():
    app = create_app_v2()
    app.testing = True
    with app.test_client() as c:
        fam = urllib.parse.quote('μ-TRTX-Hh2a')
        r = c.get(f'/v2/family-peptides/{fam}')
        assert r.status_code == 200
        data = r.get_json()
        assert data and data.get('success') is True
        payload = data.get('data')
        assert payload and payload.get('family_type') in {'original_plus_modified', 'multiple_originals'}
        assert 'total_count' in payload


def test_family_peptides_multiple_originals_beta_v2():
    app = create_app_v2()
    app.testing = True
    with app.test_client() as c:
        r = c.get('/v2/family-peptides/β-TRTX')
        assert r.status_code == 200
        data = r.get_json()
        assert data and data.get('success') is True
        payload = data.get('data')
        assert payload and payload.get('family_type') == 'multiple_originals'
        assert isinstance(payload.get('all_peptides'), list)


def test_family_dipoles_structure_v2():
    app = create_app_v2()
    app.testing = True
    with app.test_client() as c:
        fam = urllib.parse.quote('μ-TRTX-Hh2a')
        r = c.get(f'/v2/family-dipoles/{fam}')
        assert r.status_code == 200
        data = r.get_json()
        assert data and data.get('success') is True
        payload = data.get('data')
        assert payload and set(['family', 'dipole_results', 'summary', 'errors']).issubset(payload.keys())
        # If there are results, check shape of first entry
        dr = payload.get('dipole_results')
        if dr:
            first = dr[0]
            assert set(['peptide_id', 'peptide_code', 'pdb_data', 'dipole_data']).issubset(first.keys())
