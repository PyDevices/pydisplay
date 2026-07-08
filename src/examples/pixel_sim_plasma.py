"""
pixel_sim_plasma.py — flowing rainbow plasma on the NeoPixel simulator.

A classic demoscene plasma effect on the ``pixel_sim`` LED matrix.  Per pixel we
sum a few sine waves in x, y, and (x+y), offset by an animated time value, then
map the result through the ``palettes`` ``wheel`` (full-spectrum rainbow).

The sines are precomputed into a 256-entry integer table and combined with plain
index math (no per-pixel float ``sin``), so it stays fast and MCU-friendly.

``runtime.poll()`` runs every frame so the desktop window stays closable.

Run it as the main program to loop forever (closes with the window / Ctrl-C):

    cd src && python -c "import lib.path, runpy; runpy.run_path('examples/pixel_sim_plasma.py', run_name='__main__')"

Plain ``import pixel_sim_plasma`` renders a single frame and returns.
"""

import math
import time

from graphics import RGB565, FrameBuffer
from multimer import sleep_ms
from palettes import get_palette
from pixel_sim import display_drv, runtime

GRID_W = display_drv.width
GRID_H = display_drv.height

FRAME_MS = 20
TIME_STEP = 3  # how fast the field animates

# 256-entry integer sine table, 0..255 (one full period over the index range).
_SIN = [int((math.sin(i * math.pi / 128.0) + 1.0) * 127.5) for i in range(256)]
_MASK = 0xFF

# Full-spectrum rainbow, 256 colors so a summed field maps straight to an index.
_pal = get_palette(name="wheel", color_depth=16, length=256)

# Grid-sized RGB565 buffer; composited each frame then blitted to the LEDs.
_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)

# Precompute the per-column base phase (x term is time-independent in shape,
# only the time offset moves it), reused across rows each frame.
_X1 = [(x * 6) & _MASK for x in range(GRID_W)]
_X2 = [(x * 3) & _MASK for x in range(GRID_W)]

try:
    import pydisplay_test_mode  # type: ignore[import-not-found]

    _TEST_DURATION_S = pydisplay_test_mode.DURATION_S if pydisplay_test_mode.ENABLED else None
except ImportError:
    _TEST_DURATION_S = None


_START = time.time()


def _stop():
    """Poll input so the window closes; True when quitting or the test times out."""
    if runtime is not None:
        runtime.poll()
        if runtime.quit_requested:
            return True
    if _TEST_DURATION_S is not None and time.time() - _START >= _TEST_DURATION_S:
        return True
    return False


def _render(t):
    sin = _SIN
    pal = _pal
    pixel = _dest.pixel
    x1 = _X1
    x2 = _X2
    for y in range(GRID_H):
        # Row terms: independent of x, so lift them out of the inner loop.
        yr = (sin[(y * 6 - t) & _MASK] + sin[(y * 3 + t * 2) & _MASK]) & _MASK
        yd = (y * 5) & _MASK
        tx = t & _MASK
        txy = t & _MASK
        for x in range(GRID_W):
            v = (
                sin[(x1[x] + tx) & _MASK]
                + yr
                + sin[(x2[x] + yd + txy) & _MASK]
            )
            pixel(x, y, pal[v & _MASK])


_t = 0


def main():
    """Render one frame (advance the field, present, pace)."""
    global _t
    _render(_t)
    display_drv.blit_rect(_dest.buffer, 0, 0, GRID_W, GRID_H)
    display_drv.show()
    _t += TIME_STEP
    sleep_ms(FRAME_MS)


main()  # one frame; importing the module never loops forever

if __name__ == "__main__":
    try:
        while not _stop():
            main()
    except KeyboardInterrupt:
        pass
