import os
import sys

# Ensure project root is on sys.path so `src.*` imports resolve in all launch modes
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.interfaces.http.flask.app import create_app_v2

app = create_app_v2()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5001'))
    debug = os.getenv('DEBUG', '1') not in ('0', 'false', 'False')
    app.run(host=host, port=port, debug=debug)
