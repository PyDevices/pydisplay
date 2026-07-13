import sys

wd = "examples/tower_climb"
if wd not in sys.path:
    sys.path.append(wd)
from . import tower_climb  # noqa: F401 — gallery/kit entry: import tower_climb
