# multimer types: all
# pyscript binaries: assets/font_8x8.bin, assets/font_8x14.bin, assets/font_8x16.bin
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


def main():
    """
    The big show!
    """
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

    while True:
        for rotation in range(4):
            scale = rotation + 1
            display_drv.rotation = rotation * 90
            width, height = display_drv.width, display_drv.height
            # display_drv.fill_rect(0, 0, width, height, 0x0000)

            col_max = width - max_width * scale * text_len
            row_max = height - max_height * scale
            if col_max < 0 or row_max < 0:
                raise RuntimeError("This font is too big to display on this screen.")

            for _ in range(iterations):
                write(
                    fonts[randint(0, len(fonts) - 1)],
                    write_text,
                    randint(0, col_max),
                    randint(0, row_max),
                    pal[randint(0, len(pal) - 1)],
                    pal[randint(0, len(pal) - 1)],
                    scale,
                )
                display_drv.show()
                if runtime:
                    runtime.poll()
                if runtime.quit_requested if runtime else False:
                    return


main()
