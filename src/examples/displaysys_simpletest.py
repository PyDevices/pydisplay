# pyscript gallery: all
from board_config import display_drv, runtime
from random import getrandbits
from graphics import Area
from multimer.loop import run_forever

button_area = Area(display_drv.fill_rect(10, 10, 100, 100, 0xF800))
display_drv.show()


def poll():
    if runtime.quit_requested:
        return True
    if elist := runtime.poll():
        for e in elist:
            if e.type == runtime.events.QUIT:
                return True
            if e.type == runtime.events.MOUSEBUTTONDOWN:
                if button_area.contains(e.pos):
                    display_drv.fill_rect(*button_area, getrandbits(16))
                    print(f"Button pressed at {e.pos}")
                    display_drv.show()
    return False


# run_forever blocks on desktop/MCU but yields to the event loop on PyScript
# and Jupyter (runtime.timer_async), so the browser main thread stays live.
run_forever(poll, delay_ms=20)