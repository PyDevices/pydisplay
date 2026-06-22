# multimer types: untested
import board_config
import pdwidgets as pd
from pdwidgets.console import Console


pd.DEBUG = False
pd.MARK_UPDATES = False
pd.init_timer(10)  # Remove this line to use polled mode in a while loop


display = pd.Display(board_config.display_drv, board_config.broker, 40, 40)
screen = pd.Screen(display, visible=False)

if screen.partitioned:
    top, bottom, main = screen.top, screen.bottom, screen.main
else:
    top = bottom = main = screen

console = Console(screen)
console.clear()
screen.visible = True

i = 1
while i < 60:
    console.write(
        f"{i}:  vscroll={display.vscroll}, y_rel={console._cursor_y_rel}, y_pos={console._cursor_y_pos}\n"
    )
    if not display.timer:
        pd.tick()
    # console.by_char = not console.by_char
    i += 1
