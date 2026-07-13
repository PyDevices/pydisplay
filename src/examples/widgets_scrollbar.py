import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False


display = pd.Display(board_config.display_drv, board_config.runtime, 40, 40)
screen = pd.Screen(display, visible=False)

if screen.partitioned:
    top, bottom, main = screen.top, screen.bottom, screen.main
else:
    top = bottom = main = screen

s_left = pd.ScrollBar(main, value=0.5, vertical=True, align=pd.ALIGN.LEFT, reverse=True)
s_right = pd.ScrollBar(main, value=0.5, vertical=True, align=pd.ALIGN.RIGHT)
s_top = pd.ScrollBar(top, value=0.5, align=pd.ALIGN.BOTTOM, reverse=True)
s_bottom = pd.ScrollBar(bottom, value=0.5, align=pd.ALIGN.TOP)


screen.visible = True

board_config.runtime.run_forever()
