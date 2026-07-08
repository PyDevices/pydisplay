"""
pixel_sim_fire.py — cellular flame effect on the NeoPixel simulator.

The bottom row is a hot ember source; every frame each cell above becomes the
average of the cells below it, minus a small cooling constant, so heat rises and
flickers.  Heat (0..255) maps through a black -> red -> orange -> yellow -> white
fire palette precomputed once into an RGB565 lookup table.

``runtime.poll()`` runs every frame so the desktop window stays closable.

Run it as the main program to loop forever (closes with the window / Ctrl-C):

    cd src && python -c "import lib.path, runpy; runpy.run_path('examples/pixel_sim_fire.py', run_name='__main__')"

Plain ``import pixel_sim_fire`` renders a single frame and returns.
"""

import time
from random import getrandbits

from displaysys import color565
from graphics import RGB565, FrameBuffer
from multimer import sleep_ms
from pixel_sim import display_drv, runtime

GRID_W = display_drv.width
GRID_H = display_drv.height

FRAME_MS = 30
COOLING = 3  # subtracted per row as heat rises; higher = shorter flames


def _fire_color(i):
    """Map heat 0..255 to a fire gradient (black->red->yellow->white)."""
    if i < 64:
        return color565(i * 4, 0, 0)
    if i < 128:
        return color565(255, (i - 64) * 4, 0)
    if i < 192:
        return color565(255, 255, (i - 128) * 4)
    return color565(255, 255, 255)


# Precomputed heat -> RGB565 lookup (256 entries).
_FIRE = [_fire_color(i) for i in range(256)]

# Heat field (one byte per cell) and the RGB565 frame we blit to the LEDs.
_heat = bytearray(GRID_W * GRID_H)
_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)

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


def _seed_source():
    base = (GRID_H - 1) * GRID_W
    for x in range(GRID_W):
        # Mostly white-hot with occasional cooler gaps for a lively base.
        _heat[base + x] = 255 if getrandbits(3) else 160 + getrandbits(6)


def _propagate():
    w = GRID_W
    heat = _heat
    for y in range(GRID_H - 1):
        row = y * w
        below = row + w
        for x in range(w):
            b = below + x
            left = b - 1 if x > 0 else b
            right = b + 1 if x < w - 1 else b
            below2 = b + w if y + 2 < GRID_H else b
            v = (heat[b] + heat[left] + heat[right] + heat[below2]) // 4 - COOLING
            heat[row + x] = v if v > 0 else 0


def _paint():
    heat = _heat
    fire = _FIRE
    pixel = _dest.pixel
    for y in range(GRID_H):
        row = y * GRID_W
        for x in range(GRID_W):
            pixel(x, y, fire[heat[row + x]])


def main():
    """Render one frame (reseed embers, propagate heat, present, pace)."""
    _seed_source()
    _propagate()
    _paint()
    display_drv.blit_rect(_dest.buffer, 0, 0, GRID_W, GRID_H)
    display_drv.show()
    sleep_ms(FRAME_MS)


main()  # one frame; importing the module never loops forever

if __name__ == "__main__":
    try:
        while not _stop():
            main()
    except KeyboardInterrupt:
        pass
