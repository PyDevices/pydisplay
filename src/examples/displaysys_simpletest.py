# multimer types: all
from board_config import display_drv, runtime
from random import getrandbits
from graphics import Area

button_area = Area(display_drv.fill_rect(10, 10, 100, 100, 0xF800))
display_drv.show()
while True:
    if runtime.quit_requested:
        break
    if elist := runtime.poll():
        quit_requested = False
        for e in elist:
            if e.type == runtime.events.QUIT:
                quit_requested = True
                break
            if e.type == runtime.events.MOUSEBUTTONDOWN:
                if button_area.contains(e.pos):
                    display_drv.fill_rect(*button_area, getrandbits(16))
                    print(f"Button pressed at {e.pos}")
                    display_drv.show()
        if quit_requested:
            break