import sys

wd = "examples/tiny_toasters"
if wd not in sys.path:
    sys.path.append(wd)
from . import tiny_toasters
