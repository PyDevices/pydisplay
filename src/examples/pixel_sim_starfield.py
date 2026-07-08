"""
pixel_sim_starfield.py — 3D starfield flying toward the viewer.

Stars stream out of a central vanishing point: each has a fixed ``x``/``y`` in
world space and a depth ``z`` that shrinks every frame.  Perspective projection
(``sx = W//2 + x*FOCAL//z``) spreads them outward and accelerates them as they
approach, while brightness scales inversely with ``z`` so near stars burn bright
white and distant ones fade to dim blue.  A star respawns at ``ZMAX`` with fresh
random ``x``/``y`` once it passes the viewer or projects off-screen.

All projection is integer math (no per-pixel floats) for MCU friendliness.

``runtime.poll()`` runs every frame so the desktop window stays closable.

Run it as the main program to loop forever (closes with the window / Ctrl-C):

    cd src && python -c "import lib.path, runpy; runpy.run_path('examples/pixel_sim_starfield.py', run_name='__main__')"

Plain ``import pixel_sim_starfield`` renders a single frame and returns.
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
NUM_STARS = 80
FOCAL = 48  # projection focal length; larger = flatter approach
ZMAX = 255  # spawn depth (also caps brightness scaling)
ZMIN = 8  # respawn once a star is closer than this
SPEED = 4  # depth decrease per frame
BLACK = 0x0000

# Brightness ramp keyed by depth bucket: near stars are white, far stars are a
# dim blue so the field reads as receding.  Precomputed to keep the loop float-free.
_TINT = [color565(255 - z, 255 - z, 255) for z in range(ZMAX + 1)]


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


def _spawn():
    return [_randint(-GRID_W, GRID_W), _randint(-GRID_H, GRID_H), ZMAX]


_stars = [_spawn() for _ in range(NUM_STARS)]

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
    cx = GRID_W // 2
    cy = GRID_H // 2
    tint = _TINT
    for star in _stars:
        star[2] -= SPEED
        z = star[2]
        if z <= ZMIN:
            star[0] = _randint(-GRID_W, GRID_W)
            star[1] = _randint(-GRID_H, GRID_H)
            star[2] = ZMAX
            continue
        sx = cx + star[0] * FOCAL // z
        sy = cy + star[1] * FOCAL // z
        if 0 <= sx < GRID_W and 0 <= sy < GRID_H:
            pixel(sx, sy, tint[z])
        else:
            star[0] = _randint(-GRID_W, GRID_W)
            star[1] = _randint(-GRID_H, GRID_H)
            star[2] = ZMAX


def main():
    """Render one frame (advance the stars, present, pace)."""
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
