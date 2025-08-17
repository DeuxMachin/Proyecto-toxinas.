import sys, os
root = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
sys.path.insert(0, root)
from app import create_app

app = create_app()
with app.test_client() as c:
    r = c.get('/v2/export/residues/nav1_7/7?granularity=CA&long=5&threshold=10.0')
    print('residues', r.status_code, r.headers.get('Content-Type'))
    r = c.get('/v2/export/segments_atomicos/7?granularity=atom&long=5&threshold=10.0')
    print('segments', r.status_code, r.headers.get('Content-Type'))
