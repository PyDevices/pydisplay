from board_config import display_drv, runtime
from multimer.loop import run_forever
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


# The palette is static: draw it once, then just service events / quit.
main()


def poll():
    if runtime:
        runtime.poll()
        if runtime.quit_requested:
            return True
    return False


# run_forever blocks on desktop/MCU but yields to the event loop on PyScript
# and Jupyter (runtime.timer_async), so the browser main thread stays live.
run_forever(poll, delay_ms=100)
