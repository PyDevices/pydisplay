"""
pixel_sim_scroll.py — rainbow marquee + gradient scene on the NeoPixel simulator.

Larger LED grid (64x16 by default) driven by ``pixel_sim`` / ``PixelDisplay``.

Loop:
  1. Scroll rainbow text (one ``palettes`` wheel color per character, rendered
     once with ``text8`` — the ``font_simpletest.py`` render-to-buffer method)
     all the way across and off the left edge.
  2. Paint a vertical ``graphics.gradient_rect`` sunset and draw a sun on top
     with ``graphics.circle``; hold it for a moment.
  3. Repeat.

``runtime.poll()`` runs every frame so the desktop window stays closable.

Run it as the main program to loop forever (closes with the window / Ctrl-C):

    cd src && python -c "import lib.path, runpy; runpy.run_path('examples/pixel_sim_scroll.py', run_name='__main__')"

Plain ``import pixel_sim_scroll`` runs a single scroll+gradient cycle and returns.
"""

import time

import graphics
from graphics import RGB565, FrameBuffer, text8
from multimer import sleep_ms
from palettes import get_palette
from pixel_sim import display_drv, runtime

CHAR_W = 8
FONT_H = 8
GRID_W = display_drv.width
GRID_H = display_drv.height
Y = (GRID_H - FONT_H) // 2

FRAME_MS = 30
SCROLL_STEP = 3  # pixels per frame — higher is a faster marquee

TEXT = "PyDisplay * rainbow marquee * "
SRC_W = len(TEXT) * CHAR_W

# Sunset scene colors (RGB565): warm orange sky fading to deep purple, yellow sun.
SKY_TOP = 0xFB60
SKY_BOTTOM = 0x480F
SUN = 0xFFE0
SUN_EDGE = 0xFD20
HOLD_FRAMES = 150  # ~4.5s pause on the gradient scene

# One wheel color per character across the full spectrum.
_pal = get_palette(name="wheel", color_depth=16, length=len(TEXT))

# Render the whole string once (text8 into a wide off-screen buffer, x >= 0).
_src = FrameBuffer(bytearray(SRC_W * GRID_H * 2), SRC_W, GRID_H, RGB565)
_src.fill(0x0000)
for _i, _ch in enumerate(TEXT):
    text8(_src, _ch, _i * CHAR_W, Y, _pal[_i])

# Grid-sized scratch composited each frame, then blitted to the LED grid.
_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)

try:
    import pydisplay_test_mode  # type: ignore[import-not-found]

    _TEST_DURATION_S = pydisplay_test_mode.DURATION_S if pydisplay_test_mode.ENABLED else None
except ImportError:
    _TEST_DURATION_S = None


def _present():
    display_drv.blit_rect(_dest.buffer, 0, 0, GRID_W, GRID_H)
    display_drv.show()


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


def _draw_gradient_scene():
    graphics.gradient_rect(_dest, 0, 0, GRID_W, GRID_H, SKY_TOP, SKY_BOTTOM, vertical=True)
    r = max(2, min(GRID_W, GRID_H) // 4)
    cx, cy = GRID_W // 2, GRID_H // 2
    graphics.circle(_dest, cx, cy, r, SUN, f=True)
    graphics.circle(_dest, cx, cy, r, SUN_EDGE)


def main():
    """Run one scroll+gradient cycle (returns at the end, or early on quit)."""
    # Phase 1: text enters from the right and scrolls fully off the left.
    for scroll in range(0, GRID_W + SRC_W + 1, SCROLL_STEP):
        _dest.fill(0x0000)
        _dest.blit(_src, GRID_W - scroll, 0)
        _present()
        if _stop():
            return
        sleep_ms(FRAME_MS)

    # Phase 2: gradient sunset with a sun on top, held for a beat.
    _draw_gradient_scene()
    _present()
    for _ in range(HOLD_FRAMES):
        if _stop():
            return
        sleep_ms(FRAME_MS)


main()  # one cycle; importing the module never loops forever

if __name__ == "__main__":
    try:
        while not _stop():
            main()
    except KeyboardInterrupt:
        pass
