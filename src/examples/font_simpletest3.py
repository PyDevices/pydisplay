# pyscript gallery: all
# pyscript binaries: assets/font_8x8.bin, assets/font_8x14.bin, assets/font_8x16.bin
"""
font_simpletest3.py -- Simple test of the Font class.
inspired by Russ Hughes's hello.py

Rendering path (string → dirty blit):
  Font.text draws each glyph with per-pixel fill_rect into a full-screen
  DisplayBuffer in RAM. display.show(dirty) blits only the dirty rectangle
  (row by row) to display_drv, then display_drv.show() presents the frame.
  Fastest of the three variants because most work stays in RAM and upload is
  limited to the changed region.
"""

from board_config import display_drv, runtime
from graphics import Font
from random import getrandbits
from displaybuf import DisplayBuffer
from palettes import get_palette
from multimer.loop import run_forever


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


display = DisplayBuffer(display_drv)

BPP = display.color_depth // 8  # Bytes per pixel


def write(font, string, x, y, fg_color, bg_color, scale):
    """Render string in DisplayBuffer RAM, then blit only the dirty area to the display."""
    dirty = font.text(display, string, x, y, fg_color, scale)
    display.show(dirty)
    display_drv.show()


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
        display.rotation = st["rotation"] * 90
        width, height = display.width, display.height
        st["col_max"] = width - max_width * st["scale"] * text_len
        st["row_max"] = height - max_height * st["scale"]
        if st["col_max"] < 0 or st["row_max"] < 0:
            raise RuntimeError("This font is too big to display on this screen.")
        st["count"] = 0
        st["rotation"] = (st["rotation"] + 1) % 4

    def poll():
        if runtime:
            runtime.poll()
            if runtime.quit_requested:
                return True
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
        st["count"] += 1
        return False

    return poll


def main():
    """
    The big show!
    """
    # run_forever blocks on desktop/MCU but yields to the event loop on PyScript
    # and Jupyter (runtime.timer_async), so the browser main thread stays live.
    run_forever(_setup(), delay_ms=1)


main()
