# multimer types: all
# pyscript files: rotations.py
"""
rotations.py
============

.. figure:: ../_static/rotations.jpg
    :align: center

    Test for rotations and colors.

Rotates the display 0, 90, 180, and 270 degrees and displays the rotation
number and the color of the display background.

.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `st7789py`
    - `tft_config`
    - vga1_16x16

"""

from multimer import sleep_ms
import tft_config
import tft_text
import vga1_16x16 as font

palette = tft_config.palette


def center_on(display, using_font, text, y, fg, bg):
    """
    Center the text on the display
    """
    x = (display.width - len(text) * font.WIDTH) // 2
    tft_text.text(display, using_font, text, x, y, fg, bg)


def clear_screen(display, color):
    """
    Clear the screen by drawing rectangles starting from the center of the display
    and working towards the edges.

    Args:
        display (tft): The display object to clear.
        color (int): The color to use for the rectangles.
    """
    width = display.width
    height = display.height
    x_center = width // 2
    y_center = height // 2

    for i in range(min(x_center, y_center)):
        x = x_center - i
        y = y_center - i
        rect_width = 2 * i + 1
        rect_height = 2 * i + 1
        display.rect(x, y, rect_width, rect_height, color)


def main():
    """
    The big show!
    """
    tft = tft_config.config(tft_config.WIDE)

    colors = (
        ("Red", palette.RED, palette.WHITE),
        ("Green", palette.GREEN, palette.BLACK),
        ("Blue", palette.BLUE, palette.WHITE),
        ("Black", palette.BLACK, palette.WHITE),
        ("White", palette.WHITE, palette.BLACK),
        ("Yellow", palette.YELLOW, palette.BLACK),
        ("Cyan", palette.CYAN, palette.BLACK),
        ("Magenta", palette.MAGENTA, palette.BLACK),
    )

    color_idx = 0
    while True:
        for rotation in range(4):
            tft.rotation = rotation
            height = tft.height
            width = tft.width
            fg = colors[color_idx][2]
            bg = colors[color_idx][1]

            tft.draw.fill(bg)

            tft.draw.rect(0, 0, width, height, palette.WHITE)
            center_on(tft, font, "Rotation", height // 3 - font.HEIGHT // 2, fg, bg)
            center_on(tft, font, str(rotation), height // 2 - font.HEIGHT // 2, fg, bg)
            center_on(
                tft,
                font,
                colors[color_idx][0],
                height // 3 * 2 - font.HEIGHT // 2,
                fg,
                bg,
            )
            tft.show()
            color_idx = (color_idx + 1) % len(colors)
            sleep_ms(2000)


main()
