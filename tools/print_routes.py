import sys
import os
root = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
sys.path.insert(0, root)
from app import create_app
app = create_app()
print('URL RULES:')
for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
    print(str(r))
