import sys

wd = "examples/proverbs"
if wd not in sys.path:
    sys.path.append(wd)
from . import proverbs
