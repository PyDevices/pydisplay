import sys

wd = "examples/roku_remote"
if wd not in sys.path:
    sys.path.append(wd)
from . import roku_remote  # noqa: F401 — gallery/kit entry: import roku_remote
