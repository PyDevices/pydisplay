# multimer types: queued, sync
from board_config import broker, display_drv
from eventsys import poll_quit_discarding_others
from multimer import pump, sleep_ms
from palettes import get_palette

if display_drv.requires_byteswap:
    needs_swap = display_drv.disable_auto_byteswap(True)
else:
    needs_swap = False

display_drv.rotation = 0

palette = get_palette(name="wheel", swapped=needs_swap, length=256, saturation=1.0)

line_height = 2

i = 0


def main():
    global i
    for color in palette:
        if i >= display_drv.height:
            display_drv.vscsad((line_height + i) % display_drv.height)
        display_drv.fill_rect(0, i % display_drv.height, display_drv.width, line_height, color)
        display_drv.show()
        pump()
        if poll_quit_discarding_others(broker):
            break
        sleep_ms(1)
        i += line_height


def loop():
    while True:
        main()


loop()
