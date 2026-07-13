from board_config import display_drv, runtime
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


poll = _setup()


def _tick(_=None):
    poll()


runtime.on_tick(_tick, period=1, async_=runtime.timer_async)
runtime.run_forever()
