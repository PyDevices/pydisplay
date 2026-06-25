# multimer types: queued, sync
# pyscript files: palettes_material.py
from board_config import display_drv
from multimer import run_queued, sleep_ms
from palettes import get_palette

if display_drv.requires_byteswap:
    needs_swap = display_drv.disable_auto_byteswap(True)
else:
    needs_swap = False

display_drv.rotation = 0

palette = get_palette(name="material_design", color_depth=16, swapped=needs_swap)


def main():
    line_height = 1
    for i, color in enumerate(palette):
        display_drv.fill_rect(0, i * line_height, display_drv.width, line_height, color)
    display_drv.show()


while True:
    main()
    run_queued()
    sleep_ms(1)
