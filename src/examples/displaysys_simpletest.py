# multimer types: all
from board_config import display_drv, broker
from random import getrandbits
from graphics import Area

button_area = Area(display_drv.fill_rect(10, 10, 100, 100, 0xF800))
display_drv.show()
while True:
    if elist := broker.poll():
        for e in elist:
            if e.type == broker.events.QUIT:
                break
            if e.type == broker.events.MOUSEBUTTONDOWN:
                if button_area.contains(e.pos):
                    display_drv.fill_rect(*button_area, getrandbits(16))
                    print(f"Button pressed at {e.pos}")
                    display_drv.show()