import sys, os, json
root = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
sys.path.insert(0, root)
from app import create_app

app = create_app()
with app.test_client() as c:
    for source in ['toxinas', 'nav1_7']:
        r = c.get(f'/v2/peptides?source={source}')
        print(source, r.status_code, r.is_json)
        data = r.get_json()
        print('keys', list(data.keys()))
        print('count', len(data.get('items', [])))
        if data.get('items'):
            print('first', data['items'][0])
