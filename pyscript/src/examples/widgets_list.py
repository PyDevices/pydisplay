"""
Test ListView widget
"""

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

clock = pd.DigitalClock(bottom, y=-12, align=pd.ALIGN.BOTTOM_RIGHT, visible=False)
clock_toggle = pd.ToggleButton(bottom, align_to=clock, align=pd.ALIGN.OUTER_LEFT, value=False)
status = pd.TextBox(
    bottom, y=-8, w=clock_toggle.x, align=pd.ALIGN.BOTTOM_LEFT, scale=1, value="Status: loaded."
)
clock_toggle.add_event_cb(
    pd.events.MOUSEBUTTONDOWN, lambda sender, e: clock.hide(not sender.value)
)

item_no = 1


def add_item(to_list: pd.ListView):
    global item_no
    item = pd.Button(
        to_list, label=f"Item {item_no}", icon_file=pd.icon_theme.home(pd.ICON_SIZE.LARGE)
    )
    item.add_event_cb(
        pd.events.MOUSEBUTTONDOWN,
        lambda sender, e: status.set_value(f"{sender.label.value} clicked."),
    )
    item_no += 1


def remove_item(from_list: pd.ListView):
    if from_list.children:
        from_list.children[0].parent = None
    else:
        status.value = "ListView is empty."


list_view = pd.ListView(main, w=main.width // 2, h=main.height // 2, align=pd.ALIGN.CENTER)

add = pd.Button(top, label="+ Item")
remove = pd.Button(top, label="- Item", align_to=add, align=pd.ALIGN.OUTER_RIGHT)
down = pd.IconButton(
    top, align=pd.ALIGN.TOP_RIGHT, icon_file=pd.icon_theme.down_arrow(pd.ICON_SIZE.LARGE)
)
up = pd.IconButton(
    top,
    align_to=down,
    align=pd.ALIGN.OUTER_LEFT,
    icon_file=pd.icon_theme.up_arrow(pd.ICON_SIZE.LARGE),
)

add.add_event_cb(pd.events.MOUSEBUTTONUP, lambda sender, e: add_item(list_view))
remove.add_event_cb(pd.events.MOUSEBUTTONUP, lambda sender, e: remove_item(list_view))
down.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda sender, e: list_view.scroll_down())
up.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda sender, e: list_view.scroll_up())
list_view.set_change_cb(
    lambda sender: status.set_value(f"Item {sender.value + 1} of {len(sender.children)}")
)


screen.visible = True

board_config.runtime.run_forever()
