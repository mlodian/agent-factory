"""Put the project root on sys.path so `from src import ...` works under pytest.

pytest prepends the test file's own directory, not the project root, so without
this the tests would import nothing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
