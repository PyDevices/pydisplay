# multimer types: all
# Loads the full bitmap into memory before blitting it to the display.
# Will raise a MemoryError on low memory boards # such as RP2040.
# See bmp565_scroll_sprite.py for an example of streaming one line at
# a time instead of the full bitmap.
from board_config import display_drv
from bmp565 import BMP565
from graphics import hline


try:
    bmp = BMP565("examples/assets/warrior.bmp")
except MemoryError:
    raise MemoryError("this board doesn't have enough RAM to load the full image")

print(f"{bmp.width=}, {bmp.height=}, {bmp.bpp=}")
display_drv.blit_rect(bmp[0 : bmp.width, 0 : bmp.height], 0, 0, bmp.width, bmp.height)

hline(bmp, 0, bmp.height // 2, bmp.width, 0xFFFF)
display_drv.blit_rect(bmp[:], bmp.width, 0, bmp.width, bmp.height)

display_drv.show()
