import os
import sys

# Add project root to sys.path to resolve 'src' package
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.interfaces.http.flask.app import create_app_v2

# WSGI entrypoint
application = create_app_v2()
