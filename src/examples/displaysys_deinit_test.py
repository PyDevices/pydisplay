"""displaysys_deinit_test.py — verify idempotent display teardown."""

import sys

_file = __file__.replace("\\", "/").split("/")
if len(_file) >= 2 and _file[-2] == "examples":
    _src = "/".join(_file[:-2]) or "."
else:
    _src = "."
if _src not in sys.path:
    sys.path.insert(0, _src)

import lib.path  # noqa: F401

from board_config import display_drv

cls = display_drv.__class__.__name__

display_drv.fill(0xF800)
display_drv.show()

display_drv.deinit()
assert display_drv._deinitialized, "_deinitialized not set after deinit()"

display_drv.deinit()  # idempotent — must not raise or re-run cleanup

print(f"DEINIT_OK class={cls}")
