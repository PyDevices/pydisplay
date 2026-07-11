import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False
pd.init_timer(10)  # Remove this line to use polled mode in a while loop


display = pd.Display(board_config.display_drv, board_config.runtime, 40, 40)
screen = pd.Screen(display, visible=False)

if screen.partitioned:
    top, bottom, main = screen.top, screen.bottom, screen.main
else:
    top = bottom = main = screen

home = pd.IconButton(
    top, align=pd.ALIGN.TOP_LEFT, icon_file=pd.icon_theme.home(pd.ICON_SIZE.LARGE)
)
clock = pd.DigitalClock(bottom, y=-12, align=pd.ALIGN.BOTTOM_RIGHT, visible=False)
clock_toggle = pd.ToggleButton(bottom, align_to=clock, align=pd.ALIGN.OUTER_LEFT, value=False)
status = pd.TextBox(
    bottom, y=-8, w=clock_toggle.x, align=pd.ALIGN.BOTTOM_LEFT, scale=1, value="Status: loaded."
)
clock_toggle.add_event_cb(
    pd.events.MOUSEBUTTONDOWN, lambda sender, e: clock.hide(not sender.value)
)
button = pd.Button(main, label="Button")
button.add_event_cb(
    pd.events.MOUSEBUTTONDOWN, lambda sender, e: status.set_value("Button clicked!")
)
button.add_event_cb(
    pd.events.MOUSEBUTTONUP, lambda sender, e: status.set_value("Button released.")
)
screen.visible = True


pd.run_forever()
