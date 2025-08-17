import sys, os
root = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
sys.path.insert(0, root)
from app import create_app

app = create_app()
with app.test_client() as c:
    r = c.post('/v2/dipole/nav1_7/7')
    print('dipole', r.status_code, r.is_json)
    if r.is_json:
        data = r.get_json()
        print('keys', list(data.keys()))
        if 'dipole' in data:
            print('dipole_keys', list(data['dipole'].keys())[:5])
