"""
pixel_sim — desktop simulator for addressable-LED matrices (NeoPixel / DotStar).

Develop a pixeldisplay app without hardware.  ``PixelDisplay`` draws into a
``graphics.FrameBuffer`` (RGB888, one cell per LED); on ``show()`` that
framebuffer is scaled up and painted as an LED matrix onto the shared desktop /
PyScript / notebook display from ``lib/board_config.py``.

The board config for this simulator is just::

    from pixel_sim import display_drv, runtime

Poll ``runtime`` each frame (``runtime.poll()`` / ``runtime.quit_requested``) so
the desktop window stays closable — the simulator drives its own draw loop, so
nothing polls for you.

Grid size defaults to 64x16; override with ``PIXEL_SIM_WIDTH`` /
``PIXEL_SIM_HEIGHT`` (honored on CPython and MicroPython).
"""

import os

import graphics
from displaysys import color565
from displaysys.pixeldisplay import PixelDisplay

# ``lib/`` is on sys.path (via lib/path.py), so import the host board_config bare
# — ``from lib import board_config`` fails on MicroPython (no namespace packages).
import board_config as _host  # noqa: E402


def _env_int(name, default):
    # MicroPython's ``os`` has no ``environ``; fall back to ``getenv``.
    env = getattr(os, "environ", None)
    value = env.get(name) if env is not None else None
    if value is None and hasattr(os, "getenv"):
        try:
            value = os.getenv(name)
        except Exception:
            value = None
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


PIXEL_WIDTH = _env_int("PIXEL_SIM_WIDTH", 64)
PIXEL_HEIGHT = _env_int("PIXEL_SIM_HEIGHT", 16)

# Reuse the standard scaled desktop/browser/notebook backend as the output surface.
# The host board_config wires its own periodic-refresh runtime; the simulator
# presents frames itself via PixelDisplay.show(), so stop that shared timer to
# avoid a redundant refresh loop (and its signal-based teardown on CPython).
# The runtime itself is kept (re-exported below) so apps can still poll it for
# window-close / quit events; poll() is independent of the timer.
_backend = _host.display_drv
_host_runtime = getattr(_host, "runtime", None)
if _host_runtime is not None and hasattr(_host_runtime, "stop_timer"):
    _host_runtime.stop_timer()


def _rgb565_from_888(c):
    return color565((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)


class SimPixelFramebuffer(graphics.FrameBuffer):
    """RGB888 grid framebuffer that renders scaled LED blocks to a desktop display.

    A drop-in for the ``pixel_buffer`` that :class:`PixelDisplay` wraps: it
    exposes ``width`` / ``height`` / ``rotation`` and a ``display()`` flush, but
    instead of pushing to a physical strip it paints each cell as a large square
    on ``backend`` (centered, square LEDs, dark gaps for a matrix look).
    """

    BOARD_COLOR = 0x0841  # near-black RGB565 "PCB" behind the LEDs

    def __init__(self, width, height, backend):
        self._backend = backend
        buf = bytearray(width * height * 3)
        super().__init__(buf, width, height, graphics.RGB888)
        self.rotation = 0
        self._block = max(1, min(backend.width // width, backend.height // height))
        self._gap = max(1, self._block // 8)
        self._ox = (backend.width - self._block * width) // 2
        self._oy = (backend.height - self._block * height) // 2

    def display(self):
        b = self._backend
        block = self._block
        gap = self._gap
        inner = block - 2 * gap
        b.fill(self.BOARD_COLOR)
        for y in range(self.height):
            for x in range(self.width):
                color = _rgb565_from_888(self.pixel(x, y))
                b.fill_rect(self._ox + x * block + gap, self._oy + y * block + gap, inner, inner, color)
        b.show()


_pixel_framebuf = SimPixelFramebuffer(PIXEL_WIDTH, PIXEL_HEIGHT, _backend)
display_drv = PixelDisplay(_pixel_framebuf)

# Host runtime for quit/window-close handling. Its refresh timer is stopped
# (see above); apps still call runtime.poll() each frame to stay closable.
runtime = _host_runtime
