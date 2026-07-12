"""
Visual text compare: framebuf and graphics, native C vs Python.

Run from ``src/``::

    cd src
    micropython examples/framebuf_text_compare.py

2×2 layout (320×480 default)::

    ┌─────────────────┬─────────────────┐
    │ C framebuf      │ add_ons/framebuf│  top
    ├─────────────────┼─────────────────┤
    │ graphics cmod   │ lib/graphics    │  bottom
    └─────────────────┴─────────────────┘
"""

import os
import sys

_src = os.getcwd()
if _src not in sys.path:
    sys.path.insert(0, _src)

import lib.path  # noqa: F401

from board_config import display_drv, runtime
import framebuf as native_fb
import graphics as gfx_native
from multimer.loop import run_forever

_GRAPHICS_PY_FILES = (
    "__init__.py",
    "_area.py",
    "_clip.py",
    "_blit_hooks.py",
    "_framebuf_plus.py",
    "_shapes.py",
    "_font.py",
    "_font_8x8.py",
    "_font_8x14.py",
    "_font_8x16.py",
    "_draw.py",
    "_bmp565.py",
    "_files.py",
)

W = display_drv.width
H = display_drv.height
HALF_W = W // 2
HALF_H = H // 2
BPP = 2

BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
CYAN = 0x07FF
YELLOW = 0xFFE0


def _makedirs(path):
    if not path:
        return
    parts = [p for p in path.split("/") if p]
    cur = ""
    for part in parts:
        cur = cur + "/" + part if cur else part
        try:
            os.mkdir(cur)
        except OSError:
            pass


def _basename(path):
    i = path.rfind("/")
    return path[i + 1 :] if i >= 0 else path


def _dirname(path):
    i = path.rfind("/")
    if i <= 0:
        return path if i == 0 else "."
    return path[:i]


def _stage_graphics_py():
    repo = _dirname(_src) if _basename(_src) == "src" else _src
    gfx_src = _src + "/lib/graphics"
    staging = repo + "/.cursor/compare_graphics_py"
    pkg_dir = staging + "/graphics_py"
    _makedirs(pkg_dir)

    with open(_src + "/add_ons/framebuf.py") as f:
        framebuf_code = f.read()
    with open(pkg_dir + "/framebuf.py", "w") as f:
        f.write(framebuf_code)

    for name in _GRAPHICS_PY_FILES:
        with open(gfx_src + "/" + name) as f:
            code = f.read()
        with open(pkg_dir + "/" + name, "w") as f:
            f.write(code)

    for key in list(sys.modules):
        if key == "graphics_py" or key.startswith("graphics_py."):
            del sys.modules[key]

    if staging not in sys.path:
        sys.path.insert(0, staging)

    import graphics_py

    return graphics_py


def _make_fb(FB, w, h, rgb565):
    buf = bytearray(w * h * BPP)
    return FB(buf, w, h, rgb565), buf


def _draw_framebuf_panel(fb, label, strings):
    fb.fill(BLACK)
    fb.text(label, 4, 4, WHITE)
    for text, x, y, color in strings:
        fb.text(text, x, y, color)


def _draw_graphics_panel(gfx, label):
    buf = bytearray(HALF_W * HALF_H * BPP)
    fb = gfx.FrameBuffer(buf, HALF_W, HALF_H, gfx.RGB565)
    fb.fill(BLACK)
    gfx.text8(fb, label, 2, 2, WHITE)
    gfx.text8(fb, "Hi 8", 2, 14, GREEN)
    gfx.text14(fb, "A 14", 2, 26, RED)
    gfx.text16(fb, "A 16", 2, 44, CYAN)
    gfx.text(fb, "text", 2, 64, YELLOW)
    fb.text("FBtxt", 2, 80, WHITE)
    return buf


# --- framebuf: Python drop-in via exec ---
_py_ns = {"__name__": "framebuf_py"}
with open("add_ons/framebuf.py") as _f:
    exec(_f.read(), _py_ns)
PyFB = _py_ns["FrameBuffer"]

FB_STRINGS = (
    ("framebuf", 4, 22, WHITE),
    ("ABCDEFG", 4, 38, RED),
    ("Hi!", 4, 54, GREEN),
    ("0123456789", 4, 70, CYAN),
)

fb_native, buf_native = _make_fb(native_fb.FrameBuffer, HALF_W, HALF_H, native_fb.RGB565)
fb_python, buf_python = _make_fb(PyFB, HALF_W, HALF_H, native_fb.RGB565)
_draw_framebuf_panel(fb_native, "C framebuf", FB_STRINGS)
_draw_framebuf_panel(fb_python, "py framebuf", FB_STRINGS)

# --- graphics: cmod vs staged lib/graphics ---
gfx_python = _stage_graphics_py()
buf_gfx_native = _draw_graphics_panel(gfx_native, "gfx cmod")
buf_gfx_python = _draw_graphics_panel(gfx_python, "gfx python")

display_drv.fill(BLACK)
display_drv.blit_rect(buf_native, 0, 0, HALF_W, HALF_H)
display_drv.blit_rect(buf_python, HALF_W, 0, HALF_W, HALF_H)
display_drv.blit_rect(buf_gfx_native, 0, HALF_H, HALF_W, HALF_H)
display_drv.blit_rect(buf_gfx_python, HALF_W, HALF_H, HALF_W, HALF_H)

for y in range(H):
    display_drv.pixel(HALF_W, y, WHITE)
for x in range(W):
    display_drv.pixel(x, HALF_H, WHITE)

display_drv.show()

print("text compare (2x2)")
print("  top-left     = C framebuf")
print("  top-right    = add_ons/framebuf.py")
print("  bottom-left  = graphics cmod (text8/14/16, text, FB.text)")
print("  bottom-right = lib/graphics (same APIs)")
print("Close the window or press Ctrl+C here.")


def poll():
    if runtime:
        runtime.poll()
        if runtime.quit_requested:
            return True
    return False


# The comparison image is static: draw once (above) then just service events.
# run_forever blocks on desktop/MCU but yields to the event loop on PyScript
# and Jupyter (runtime.timer_async), so the browser main thread stays live.
run_forever(poll, delay_ms=50)
