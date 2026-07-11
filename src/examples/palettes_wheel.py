# pyscript gallery: all
from board_config import display_drv, runtime
from multimer.loop import run_forever
from palettes import get_palette

if display_drv.requires_byteswap:
    needs_swap = display_drv.disable_auto_byteswap(True)
else:
    needs_swap = False

display_drv.rotation = 0

palette = get_palette(name="wheel", swapped=needs_swap, length=256, saturation=1.0)

line_height = 2


def _setup():
    colors = list(palette)
    n = len(colors)
    st = {"ci": 0, "i": 0}

    def poll():
        if runtime:
            runtime.poll()
            if runtime.quit_requested:
                return True
        if st["i"] >= display_drv.height:
            display_drv.vscsad((line_height + st["i"]) % display_drv.height)
        display_drv.fill_rect(
            0, st["i"] % display_drv.height, display_drv.width, line_height, colors[st["ci"]]
        )
        display_drv.show()
        st["i"] += line_height
        st["ci"] = (st["ci"] + 1) % n
        return False

    return poll


# run_forever blocks on desktop/MCU but yields to the event loop on PyScript
# and Jupyter (runtime.timer_async), so the browser main thread stays live.
run_forever(_setup(), delay_ms=1)
