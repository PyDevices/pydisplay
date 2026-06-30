import sys

wd = "examples/alien"
if wd not in sys.path:
    sys.path.append(wd)
from . import alien
