import sys

wd = "examples/noto_fonts"
if wd not in sys.path:
    sys.path.append(wd)
from . import noto_fonts
