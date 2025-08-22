import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so that 'backend' package can be imported
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT / 'test.db'}")
