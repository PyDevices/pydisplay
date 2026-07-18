import sys

wd = "examples/car_cluster"
if wd not in sys.path:
    sys.path.append(wd)
from . import car_cluster  # noqa: F401 — gallery/kit entry: import car_cluster
from board_config import runtime

# Package import is the PyScript/gallery entry (not ``__main__``); keep LVGL alive.
runtime.run_forever()
