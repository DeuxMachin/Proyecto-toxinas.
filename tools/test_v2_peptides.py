import sys, os, json
root = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
sys.path.insert(0, root)
from app import create_app

app = create_app()
with app.test_client() as c:
    for source in ['toxinas', 'nav1_7']:
        r = c.get(f'/v2/peptides?source={source}')
        # response available in `r`; inspect in debugger if needed
        data = r.get_json()
        # keys and counts available in `data`
        if data.get('items'):
            # first item available in data['items'][0]
            pass
