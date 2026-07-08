"""
pixel_sim_matrix.py — "digital rain" on the NeoPixel simulator.

Each column has a falling head that leaves a fading green trail: a bright,
near-white head, then a gradient down to dark green, on a black background.
Columns fall at independent speeds and respawn at the top once they scroll off.

``runtime.poll()`` runs every frame so the desktop window stays closable.

Run it as the main program to loop forever (closes with the window / Ctrl-C):

    cd src && python -c "import lib.path, runpy; runpy.run_path('examples/pixel_sim_matrix.py', run_name='__main__')"

Plain ``import pixel_sim_matrix`` renders a single frame and returns.
"""

import time
from random import getrandbits

from displaysys import color565
from graphics import RGB565, FrameBuffer
from multimer import sleep_ms
from pixel_sim import display_drv, runtime

GRID_W = display_drv.width
GRID_H = display_drv.height

FRAME_MS = 45
TRAIL = 14  # trail length in cells
BLACK = 0x0000
HEAD = color565(200, 255, 200)  # near-white head

# Precompute the fading green trail (index 0 = just behind head, brightest green).
_TRAIL = [color565(0, max(40, 255 - i * (215 // TRAIL)), 0) for i in range(TRAIL)]


def _randint(a, b):
    span = b - a + 1
    if span <= 1:
        return a
    bits = 0
    n = span - 1
    while n:
        bits += 1
        n >>= 1
    return a + getrandbits(bits) % span


# Per-column head position (in 1/8 cell fixed point) and fall speed.
_head = [_randint(-GRID_H, 0) * 8 for _ in range(GRID_W)]
_speed = [_randint(3, 10) for _ in range(GRID_W)]  # eighths of a cell per frame

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


def _step():
    _dest.fill(BLACK)
    pixel = _dest.pixel
    for x in range(GRID_W):
        _head[x] += _speed[x]
        head_y = _head[x] >> 3
        for k in range(TRAIL):
            y = head_y - k
            if 0 <= y < GRID_H:
                pixel(x, y, HEAD if k == 0 else _TRAIL[k])
        if head_y - TRAIL > GRID_H:
            _head[x] = _randint(-GRID_H, 0) * 8
            _speed[x] = _randint(3, 10)


def main():
    """Render one frame (advance the rain, present, pace)."""
    _step()
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
