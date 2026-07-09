"""
pixel_sim_demos.py — NeoPixel simulator effects in one file.

Pick an effect with ``DEMO`` (``scroll``, ``plasma``, ``fire``, ``matrix``,
``starfield``, or ``reel`` for all of them in sequence).  Each effect calls
``runtime.poll()`` every frame so the desktop window stays closable.

**Simulator (default):** ``import lib.path`` from ``src/`` and run::

    cd src && python -c "import lib.path, runpy; runpy.run_path('examples/pixel_sim_demos.py', run_name='__main__')"

**Real PixelDisplay hardware:** use ``from board_config import display_drv, runtime``
instead of ``from pixel_sim import …`` (your hardware ``board_config`` must wire
``PixelDisplay``).

Plain ``import pixel_sim_demos`` runs one frame (or one scroll cycle / reel pass)
and returns.
"""

import math
import time
from random import getrandbits

import graphics
from displaysys import color565
from graphics import RGB565, FrameBuffer, text8
from multimer import sleep_ms, ticks_add, ticks_diff, ticks_ms
from palettes import get_palette
from pixel_sim import display_drv, runtime

# scroll | plasma | fire | matrix | starfield | reel
DEMO = "fire"

GRID_W = display_drv.width
GRID_H = display_drv.height

try:
    import pydisplay_test_mode  # type: ignore[import-not-found]

    _TEST_DURATION_S = pydisplay_test_mode.DURATION_S if pydisplay_test_mode.ENABLED else None
except ImportError:
    _TEST_DURATION_S = None

_START = time.time()
_REEL_START = ticks_ms()


def _stop():
    """Poll input so the window closes; True when quitting or the test times out."""
    if runtime is not None:
        runtime.poll()
        if runtime.quit_requested:
            return True
    if _TEST_DURATION_S is not None and time.time() - _START >= _TEST_DURATION_S:
        return True
    return False


def _reel_stop():
    if runtime is not None:
        runtime.poll()
        if runtime.quit_requested:
            return True
    if _TEST_DURATION_S is not None and ticks_diff(ticks_ms(), _REEL_START) >= _TEST_DURATION_S * 1000:
        return True
    return False


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


def _present(dest):
    display_drv.blit_rect(dest.buffer, 0, 0, GRID_W, GRID_H)
    display_drv.show()


# --- scroll -----------------------------------------------------------------

_CHAR_W = 8
_FONT_H = 8
_SCROLL_Y = (GRID_H - _FONT_H) // 2
_SCROLL_FRAME_MS = 30
_SCROLL_STEP = 3
_SCROLL_TEXT = "PyDisplay * rainbow marquee * "
_SCROLL_SRC_W = len(_SCROLL_TEXT) * _CHAR_W
_SKY_TOP = 0xFB60
_SKY_BOTTOM = 0x480F
_SUN = 0xFFE0
_SUN_EDGE = 0xFD20
_SCROLL_HOLD = 150

_scroll_pal = get_palette(name="wheel", color_depth=16, length=len(_SCROLL_TEXT))
_scroll_src = FrameBuffer(bytearray(_SCROLL_SRC_W * GRID_H * 2), _SCROLL_SRC_W, GRID_H, RGB565)
_scroll_src.fill(0x0000)
for _i, _ch in enumerate(_SCROLL_TEXT):
    text8(_scroll_src, _ch, _i * _CHAR_W, _SCROLL_Y, _scroll_pal[_i])
_scroll_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)


def _scroll_gradient_scene():
    graphics.gradient_rect(_scroll_dest, 0, 0, GRID_W, GRID_H, _SKY_TOP, _SKY_BOTTOM, vertical=True)
    r = max(2, min(GRID_W, GRID_H) // 4)
    cx, cy = GRID_W // 2, GRID_H // 2
    graphics.circle(_scroll_dest, cx, cy, r, _SUN, f=True)
    graphics.circle(_scroll_dest, cx, cy, r, _SUN_EDGE)


def scroll_main():
    """One scroll+gradient cycle."""
    for scroll in range(0, GRID_W + _SCROLL_SRC_W + 1, _SCROLL_STEP):
        _scroll_dest.fill(0x0000)
        _scroll_dest.blit(_scroll_src, GRID_W - scroll, 0)
        _present(_scroll_dest)
        if _stop():
            return
        sleep_ms(_SCROLL_FRAME_MS)
    _scroll_gradient_scene()
    _present(_scroll_dest)
    for _ in range(_SCROLL_HOLD):
        if _stop():
            return
        sleep_ms(_SCROLL_FRAME_MS)


# --- plasma -----------------------------------------------------------------

_PLASMA_FRAME_MS = 20
_PLASMA_TIME_STEP = 3
_PLASMA_SIN = [int((math.sin(i * math.pi / 128.0) + 1.0) * 127.5) for i in range(256)]
_PLASMA_MASK = 0xFF
_plasma_pal = get_palette(name="wheel", color_depth=16, length=256)
_plasma_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)
_PLASMA_X1 = [(x * 6) & _PLASMA_MASK for x in range(GRID_W)]
_PLASMA_X2 = [(x * 3) & _PLASMA_MASK for x in range(GRID_W)]
_plasma_t = 0


def _plasma_render(t):
    sin = _PLASMA_SIN
    pal = _plasma_pal
    pixel = _plasma_dest.pixel
    x1 = _PLASMA_X1
    x2 = _PLASMA_X2
    for y in range(GRID_H):
        yr = (sin[(y * 6 - t) & _PLASMA_MASK] + sin[(y * 3 + t * 2) & _PLASMA_MASK]) & _PLASMA_MASK
        yd = (y * 5) & _PLASMA_MASK
        tx = t & _PLASMA_MASK
        txy = t & _PLASMA_MASK
        for x in range(GRID_W):
            v = sin[(x1[x] + tx) & _PLASMA_MASK] + yr + sin[(x2[x] + yd + txy) & _PLASMA_MASK]
            pixel(x, y, pal[v & _PLASMA_MASK])


def plasma_main():
    global _plasma_t
    _plasma_render(_plasma_t)
    _present(_plasma_dest)
    _plasma_t += _PLASMA_TIME_STEP
    sleep_ms(_PLASMA_FRAME_MS)


# --- fire -------------------------------------------------------------------

_FIRE_FRAME_MS = 30
_FIRE_COOLING = 3


def _fire_color(i):
    if i < 64:
        return color565(i * 4, 0, 0)
    if i < 128:
        return color565(255, (i - 64) * 4, 0)
    if i < 192:
        return color565(255, 255, (i - 128) * 4)
    return color565(255, 255, 255)


_FIRE_LUT = [_fire_color(i) for i in range(256)]
_fire_heat = bytearray(GRID_W * GRID_H)
_fire_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)


def _fire_seed():
    base = (GRID_H - 1) * GRID_W
    for x in range(GRID_W):
        _fire_heat[base + x] = 255 if getrandbits(3) else 160 + getrandbits(6)


def _fire_propagate():
    w = GRID_W
    heat = _fire_heat
    for y in range(GRID_H - 1):
        row = y * w
        below = row + w
        for x in range(w):
            b = below + x
            left = b - 1 if x > 0 else b
            right = b + 1 if x < w - 1 else b
            below2 = b + w if y + 2 < GRID_H else b
            v = (heat[b] + heat[left] + heat[right] + heat[below2]) // 4 - _FIRE_COOLING
            heat[row + x] = v if v > 0 else 0


def _fire_paint():
    heat = _fire_heat
    fire = _FIRE_LUT
    pixel = _fire_dest.pixel
    for y in range(GRID_H):
        row = y * GRID_W
        for x in range(GRID_W):
            pixel(x, y, fire[heat[row + x]])


def fire_main():
    _fire_seed()
    _fire_propagate()
    _fire_paint()
    _present(_fire_dest)
    sleep_ms(_FIRE_FRAME_MS)


# --- matrix -----------------------------------------------------------------

_MATRIX_FRAME_MS = 45
_MATRIX_TRAIL = 14
_MATRIX_BLACK = 0x0000
_MATRIX_HEAD = color565(200, 255, 200)
_MATRIX_TRAIL = [color565(0, max(40, 255 - i * (215 // _MATRIX_TRAIL)), 0) for i in range(_MATRIX_TRAIL)]
_matrix_head = [_randint(-GRID_H, 0) * 8 for _ in range(GRID_W)]
_matrix_speed = [_randint(3, 10) for _ in range(GRID_W)]
_matrix_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)


def _matrix_step():
    _matrix_dest.fill(_MATRIX_BLACK)
    pixel = _matrix_dest.pixel
    for x in range(GRID_W):
        _matrix_head[x] += _matrix_speed[x]
        head_y = _matrix_head[x] >> 3
        for k in range(_MATRIX_TRAIL):
            y = head_y - k
            if 0 <= y < GRID_H:
                pixel(x, y, _MATRIX_HEAD if k == 0 else _MATRIX_TRAIL[k])
        if head_y - _MATRIX_TRAIL > GRID_H:
            _matrix_head[x] = _randint(-GRID_H, 0) * 8
            _matrix_speed[x] = _randint(3, 10)


def matrix_main():
    _matrix_step()
    _present(_matrix_dest)
    sleep_ms(_MATRIX_FRAME_MS)


# --- starfield --------------------------------------------------------------

_STAR_FRAME_MS = 30
_STAR_NUM = 80
_STAR_FOCAL = 48
_STAR_ZMAX = 255
_STAR_ZMIN = 8
_STAR_SPEED = 4
_STAR_BLACK = 0x0000
_STAR_TINT = [color565(255 - z, 255 - z, 255) for z in range(_STAR_ZMAX + 1)]


def _star_spawn():
    return [_randint(-GRID_W, GRID_W), _randint(-GRID_H, GRID_H), _STAR_ZMAX]


_stars = [_star_spawn() for _ in range(_STAR_NUM)]
_star_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)


def _star_step():
    _star_dest.fill(_STAR_BLACK)
    pixel = _star_dest.pixel
    cx = GRID_W // 2
    cy = GRID_H // 2
    tint = _STAR_TINT
    for star in _stars:
        star[2] -= _STAR_SPEED
        z = star[2]
        if z <= _STAR_ZMIN:
            star[0] = _randint(-GRID_W, GRID_W)
            star[1] = _randint(-GRID_H, GRID_H)
            star[2] = _STAR_ZMAX
            continue
        sx = cx + star[0] * _STAR_FOCAL // z
        sy = cy + star[1] * _STAR_FOCAL // z
        if 0 <= sx < GRID_W and 0 <= sy < GRID_H:
            pixel(sx, sy, tint[z])
        else:
            star[0] = _randint(-GRID_W, GRID_W)
            star[1] = _randint(-GRID_H, GRID_H)
            star[2] = _STAR_ZMAX


def starfield_main():
    _star_step()
    _present(_star_dest)
    sleep_ms(_STAR_FRAME_MS)


# --- reel -------------------------------------------------------------------

_REEL_DEMOS = (
    ("scroll", scroll_main),
    ("plasma", plasma_main),
    ("fire", fire_main),
    ("matrix", matrix_main),
    ("starfield", starfield_main),
)
_REEL_SECONDS = 6


def _reel_play(frame_main, seconds):
    deadline = ticks_add(ticks_ms(), int(seconds * 1000))
    while ticks_diff(deadline, ticks_ms()) > 0:
        frame_main()
        if _reel_stop():
            return True
    return False


def reel_main():
    """Play every demo once, in order (returns early on quit)."""
    for _name, frame_main in _REEL_DEMOS:
        if _reel_play(frame_main, _REEL_SECONDS):
            return


_DEMO_MAIN = {
    "scroll": scroll_main,
    "plasma": plasma_main,
    "fire": fire_main,
    "matrix": matrix_main,
    "starfield": starfield_main,
    "reel": reel_main,
}


def main():
    frame_main = _DEMO_MAIN.get(DEMO)
    if frame_main is None:
        raise ValueError(f"unknown DEMO {DEMO!r}; choose from {tuple(_DEMO_MAIN)}")
    frame_main()


main()

if __name__ == "__main__":
    try:
        while not _stop():
            main()
    except KeyboardInterrupt:
        pass
