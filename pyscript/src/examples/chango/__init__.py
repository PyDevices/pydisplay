import sys

wd = "examples/chango"
if wd not in sys.path:
    sys.path.append(wd)
from . import chango
