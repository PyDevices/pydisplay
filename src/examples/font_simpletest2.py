# pyscript skip: gallery
"""
font_simpletest2.py -- Simple test of the Font class.
inspired by Russ Hughes's hello.py

Rendering path (per-pixel → live display):
  Font.text draws each glyph with per-pixel fill_rect directly on display_drv.
  Every set font bit becomes a separate fill_rect on the hardware buffer — no
  off-screen aggregation and no partial blit. Slowest upload pattern of the
  three font_simpletest variants. display_drv.show() follows each draw.
"""

from board_config import display_drv, runtime
from graphics import Font
from random import getrandbits
from palettes import get_palette


def randint(a, b):
    span = b - a + 1
    if span <= 1:
        return a
    bits = 0
    n = span - 1
    while n:
        bits += 1
        n >>= 1
    return a + getrandbits(bits) % span


BPP = display_drv.color_depth // 8  # Bytes per pixel


def write(font, string, x, y, fg_color, bg_color, scale):
    """Draw string straight onto display_drv (per-pixel fill_rect on the live buffer)."""
    font.text(display_drv, string, x, y, fg_color, scale)


def _setup():
    pal = get_palette()

    write_text = "Hello!"
    text_len = len(write_text)
    iterations = 32

    directory = "examples/assets/"
    font1 = Font(f"{directory}font_8x8.bin")
    font2 = Font(f"{directory}font_8x14.bin")
    font3 = Font(f"{directory}font_8x16.bin")
    fonts = [font1, font2, font3]

    max_width = max([font.width for font in fonts])
    max_height = max([font.height for font in fonts])

    # count starts full so the first poll opens a fresh rotation before drawing.
    st = {"rotation": 0, "count": iterations, "scale": 1, "col_max": 0, "row_max": 0}

    def start_rotation():
        st["scale"] = st["rotation"] + 1
        display_drv.rotation = st["rotation"] * 90
        width, height = display_drv.width, display_drv.height
        st["col_max"] = width - max_width * st["scale"] * text_len
        st["row_max"] = height - max_height * st["scale"]
        if st["col_max"] < 0 or st["row_max"] < 0:
            raise RuntimeError("This font is too big to display on this screen.")
        st["count"] = 0
        st["rotation"] = (st["rotation"] + 1) % 4

    def poll():
        if st["count"] >= iterations:
            start_rotation()
            return False
        write(
            fonts[randint(0, len(fonts) - 1)],
            write_text,
            randint(0, st["col_max"]),
            randint(0, st["row_max"]),
            pal[randint(0, len(pal) - 1)],
            pal[randint(0, len(pal) - 1)],
            st["scale"],
        )
        display_drv.show()
        st["count"] += 1
        return False

    return poll


def main():
    """
    The big show!
    """
    poll = _setup()
    # Blocks on desktop/MCU but yields to the event loop on PyScript and
    # Jupyter (runtime.timer_async), so the browser main thread stays live.
    def _tick(_=None):
        poll()

    runtime.on_tick(_tick, period=1, async_=runtime.timer_async)
    runtime.run_forever()
main()
