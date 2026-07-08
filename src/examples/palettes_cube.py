# multimer types: all
from board_config import display_drv, runtime
from multimer import sleep_ms
from palettes import get_palette
from graphics import FrameBuffer, RGB565

if display_drv.requires_byteswap:
    needs_swap = display_drv.disable_auto_byteswap(True)
else:
    needs_swap = False

display_drv.rotation = 0

palette = get_palette(name="cube", size=5, color_depth=16, swapped=needs_swap)

line_height = 20
last_line = display_drv.height - line_height
scroll = 0
y = 0

BPP = display_drv.color_depth // 8
ba = bytearray(display_drv.width * line_height * BPP)
fb = FrameBuffer(ba, display_drv.width, line_height, RGB565)


def main():
    global y, scroll
    for index, color in enumerate(palette):
        if y - scroll - last_line > 0:
            scroll = (y - last_line) % display_drv.height
            display_drv.vscsad(scroll)
        name = f"{index} - {palette.color_name(index)}"
        text_color = palette.WHITE if palette.brightness(index) < 0.4 else palette.BLACK  # noqa: PLR2004
        fb.fill(color)
        fb.text16(name, 2, 2, text_color)
        display_drv.blit_rect(ba, 0, y % display_drv.height, display_drv.width, line_height)
        display_drv.show()
        sleep_ms(0)
        if runtime.quit_requested if runtime else False:
            return True
        sleep_ms(100)
        y += line_height
    return False


def loop():
    while True:
        if main():
            break


loop()
