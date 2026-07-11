from board_config import display_drv, runtime
from multimer.loop import run_forever
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

BPP = display_drv.color_depth // 8
ba = bytearray(display_drv.width * line_height * BPP)
fb = FrameBuffer(ba, display_drv.width, line_height, RGB565)


def _setup():
    entries = list(enumerate(palette))
    n = len(entries)
    st = {"idx": 0, "y": 0, "scroll": 0}

    def poll():
        if runtime:
            runtime.poll()
            if runtime.quit_requested:
                return True
        index, color = entries[st["idx"]]
        if st["y"] - st["scroll"] - last_line > 0:
            st["scroll"] = (st["y"] - last_line) % display_drv.height
            display_drv.vscsad(st["scroll"])
        name = f"{index} - {palette.color_name(index)}"
        text_color = palette.WHITE if palette.brightness(index) < 0.4 else palette.BLACK  # noqa: PLR2004
        fb.fill(color)
        fb.text16(name, 2, 2, text_color)
        display_drv.blit_rect(ba, 0, st["y"] % display_drv.height, display_drv.width, line_height)
        display_drv.show()
        st["y"] += line_height
        st["idx"] = (st["idx"] + 1) % n
        return False

    return poll


# run_forever blocks on desktop/MCU but yields to the event loop on PyScript
# and Jupyter (runtime.timer_async), so the browser main thread stays live.
run_forever(_setup(), delay_ms=100)
