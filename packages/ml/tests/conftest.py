"""Make `pathfinder_ml` and the build scripts importable without setting PYTHONPATH."""
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
for p in (ML_ROOT, ML_ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
