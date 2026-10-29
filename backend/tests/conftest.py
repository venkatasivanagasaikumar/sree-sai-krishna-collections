import os
import sys

backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ["FORCE_MOCK_DB"] = "true"
