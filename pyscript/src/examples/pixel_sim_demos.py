"""
pixel_sim_demos.py — NeoPixel simulator effects in one file.

Pick an effect with ``DEMO`` (``scroll``, ``plasma``, ``fire``, ``matrix``,
``starfield``, or ``reel`` for all of them in sequence).  Each effect calls
``runtime.poll()`` every frame so the desktop window stays closable.

**Simulator (default):** ``import lib.path`` from ``src/`` and run::

    cd src && python -c "import lib.path, runpy; runpy.run_path('add_ons/pixel_sim_demos.py', run_name='__main__')"

**Real PixelDisplay hardware:** use ``from board_config import display_drv, runtime``
instead of ``from pixel_sim import …`` (your hardware ``board_config`` must wire
``PixelDisplay``).

Plain ``import pixel_sim_demos`` runs one frame (or one scroll cycle / reel pass)
and returns.
"""

import math
from random import getrandbits

import graphics
from displaysys import color565
from graphics import RGB565, FrameBuffer, text8
from multimer import ticks_add, ticks_diff, ticks_ms
from palettes import get_palette
# Uncomment one and only one of the following two lines
#from board_config import display_drv, runtime
from pixel_sim import display_drv, runtime

# scroll | plasma | fire | matrix | starfield | reel
DEMO = "reel"

GRID_W = display_drv.width
GRID_H = display_drv.height

try:
    import pydisplay_test_mode  # type: ignore[import-not-found]

    _TEST_DURATION_S = pydisplay_test_mode.DURATION_S if pydisplay_test_mode.ENABLED else None
except ImportError:
    _TEST_DURATION_S = None

_START = ticks_ms()
_REEL_START = ticks_ms()


def _stop():
    """Poll input so the window closes; True when quitting or the test times out."""
    if runtime is not None:
        runtime.poll()
        if runtime.quit_requested:
            return True
    if _TEST_DURATION_S is not None and ticks_diff(ticks_ms(), _START) >= _TEST_DURATION_S * 1000:
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
_SCROLL_FRAME_MS = 28
_SCROLL_STEP = 4
_SCROLL_TEXT = "PyDisplay!"
_SCROLL_SRC_W = len(_SCROLL_TEXT) * _CHAR_W
_SKY_TOP = 0xFB60
_SKY_BOTTOM = 0x480F
_SUN = 0xFFE0
_SUN_EDGE = 0xFD20
_SCROLL_HOLD = 80

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
    """One scroll+gradient cycle (yields frame delays)."""
    for scroll in range(0, GRID_W + _SCROLL_SRC_W + 1, _SCROLL_STEP):
        _scroll_dest.fill(0x0000)
        _scroll_dest.blit(_scroll_src, GRID_W - scroll, 0)
        _present(_scroll_dest)
        if _stop():
            return
        yield _SCROLL_FRAME_MS
    _scroll_gradient_scene()
    _present(_scroll_dest)
    for _ in range(_SCROLL_HOLD):
        if _stop():
            return
        yield _SCROLL_FRAME_MS


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
    yield _PLASMA_FRAME_MS


# --- fire -------------------------------------------------------------------
# Doom-style heat map: seed the bottom row, each cell samples below with a
# random horizontal drift and cools. Cooling scales with grid height so a
# short LED matrix (e.g. 64x16) still tapers to black instead of filling solid.

_FIRE_FRAME_MS = 30
_FIRE_COOLING = max(2, 200 // GRID_H)


def _fire_color(i):
    """Black → red → orange → yellow → white (heat index 0..255)."""
    if i < 32:
        return color565(i * 4, 0, 0)
    if i < 96:
        return color565(128 + (i - 32), (i - 32) * 2, 0)
    if i < 160:
        return color565(255, 128 + (i - 96) * 2, 0)
    if i < 224:
        return color565(255, 255, (i - 160) * 4)
    return color565(255, 255, 255)


_FIRE_LUT = [_fire_color(i) for i in range(256)]
_fire_heat = bytearray(GRID_W * GRID_H)
_fire_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)


def _fire_seed():
    """Hot, gappy embers along the bottom row."""
    base = (GRID_H - 1) * GRID_W
    for x in range(GRID_W):
        r = getrandbits(3)
        if r == 0:
            _fire_heat[base + x] = 0
        elif r < 3:
            _fire_heat[base + x] = 96 + getrandbits(6)
        else:
            _fire_heat[base + x] = 192 + getrandbits(6)


def _fire_propagate():
    w = GRID_W
    h = GRID_H
    heat = _fire_heat
    cool = _FIRE_COOLING
    # Top → bottom so each cell reads the still-old row below (heat rises 1/frame).
    for y in range(h - 1):
        row = y * w
        below = row + w
        for x in range(w):
            drift = (getrandbits(2) % 3) - 1  # -1, 0, or +1
            sx = x + drift
            if sx < 0:
                sx = 0
            elif sx >= w:
                sx = w - 1
            v = heat[below + sx] - cool - getrandbits(2)
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
    yield _FIRE_FRAME_MS


# --- matrix -----------------------------------------------------------------

_MATRIX_FRAME_MS = 45
_MATRIX_TRAIL_LEN = 14
_MATRIX_BLACK = 0x0000
_MATRIX_HEAD = color565(200, 255, 200)
_MATRIX_TRAIL = [
    color565(0, max(40, 255 - i * (215 // _MATRIX_TRAIL_LEN)), 0) for i in range(_MATRIX_TRAIL_LEN)
]
_matrix_head = [_randint(-GRID_H, 0) * 8 for _ in range(GRID_W)]
_matrix_speed = [_randint(3, 10) for _ in range(GRID_W)]
_matrix_dest = FrameBuffer(bytearray(GRID_W * GRID_H * 2), GRID_W, GRID_H, RGB565)


def _matrix_step():
    _matrix_dest.fill(_MATRIX_BLACK)
    pixel = _matrix_dest.pixel
    for x in range(GRID_W):
        _matrix_head[x] += _matrix_speed[x]
        head_y = _matrix_head[x] >> 3
        for k in range(_MATRIX_TRAIL_LEN):
            y = head_y - k
            if 0 <= y < GRID_H:
                pixel(x, y, _MATRIX_HEAD if k == 0 else _MATRIX_TRAIL[k])
        if head_y - _MATRIX_TRAIL_LEN > GRID_H:
            _matrix_head[x] = _randint(-GRID_H, 0) * 8
            _matrix_speed[x] = _randint(3, 10)


def matrix_main():
    _matrix_step()
    _present(_matrix_dest)
    yield _MATRIX_FRAME_MS


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
    yield _STAR_FRAME_MS


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
    """Drive ``frame_main`` (a delay generator) for ``seconds``; yields frame delays."""
    deadline = ticks_add(ticks_ms(), int(seconds * 1000))
    gen = frame_main()
    while ticks_diff(deadline, ticks_ms()) > 0:
        try:
            ms = next(gen)
        except StopIteration:
            gen = frame_main()
            try:
                ms = next(gen)
            except StopIteration:
                return
        yield ms
        if _reel_stop():
            return


def reel_main():
    """Play every demo once, in order (returns early on quit)."""
    for _name, frame_main in _REEL_DEMOS:
        for ms in _reel_play(frame_main, _REEL_SECONDS):
            yield ms
            if _reel_stop():
                return


_DEMO_MAIN = {
    "scroll": scroll_main,
    "plasma": plasma_main,
    "fire": fire_main,
    "matrix": matrix_main,
    "starfield": starfield_main,
    "reel": reel_main,
}


def _demo_gen():
    frame_main = _DEMO_MAIN.get(DEMO)
    if frame_main is None:
        raise ValueError(f"unknown DEMO {DEMO!r}; choose from {tuple(_DEMO_MAIN)}")
    return frame_main()


_gen = _demo_gen()
_next_at = ticks_ms()


def _tick(_=None):
    global _gen, _next_at
    if _stop():
        runtime.request_quit()
        return
    now = ticks_ms()
    if ticks_diff(_next_at, now) > 0:
        return
    try:
        ms = next(_gen)
        _next_at = ticks_add(now, max(1, int(ms)))
    except StopIteration:
        _gen = _demo_gen()
        _next_at = now


runtime.on_tick(_tick, period=1, async_=runtime.timer_async)
runtime.run_forever()
