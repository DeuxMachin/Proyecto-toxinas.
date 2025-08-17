import sys, os, json
root = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
sys.path.insert(0, root)
from app import create_app
from app.services.database_service import DatabaseService

app = create_app()
db = DatabaseService()

# Try to get an id from nav1_7 first, fallback to toxinas
source = 'nav1_7'
peptides = db.get_all_nav1_7()
if not peptides:
    source = 'toxinas'
    peptides = db.get_all_toxinas()

assert peptides, 'No peptides found in database.'
peptide_id = peptides[0][0]

with app.test_client() as c:
    resp = c.get(f"/v2/proteins/{source}/{peptide_id}/graph?granularity=CA&long=5&threshold=10.0")
    print('STATUS', resp.status_code)
    if resp.is_json:
        data = resp.get_json()
        print('JSON_KEYS', sorted(list(data.keys())))
        if 'properties' in data:
            print('PROP_KEYS', sorted(k for k in data['properties'].keys())[:10], '...')
    else:
        print('TEXT', resp.data[:500])
