# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
"""
widgets_actions
====================================================
Showcase :class:`~pdwidgets.Menu` / :class:`~pdwidgets.ContextMenu`,
:class:`~pdwidgets.Chip` / :class:`~pdwidgets.Tag`,
:class:`~pdwidgets.SegmentedControl`, and :class:`~pdwidgets.ListView`.

AppBar plus a Menu trigger; Chip filters sit above a ListView; SegmentedControl
switches list vs grid flavour (label only).
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

toast = pd.Toast(screen)
menu = pd.ContextMenu(
    screen,
    items=[
        ("Refresh", lambda: toast.show("Refresh")),
        ("Share", lambda: toast.show("Share")),
        ("About", lambda: toast.show("About")),
    ],
)

bar = pd.AppBar(screen, title="Actions")


def open_menu(_=None, event=None):
    menu.show()


pd.Button(screen, label="Menu", x=screen.width - 56, y=4, w=52, h=28).add_event_cb(
    pd.events.MOUSEBUTTONDOWN, open_menu
)

y = bar.height + 8
seg = pd.SegmentedControl(
    screen,
    labels=["List", "Grid"],
    x=8,
    y=y,
    w=screen.width - 16,
    value=0,
)
y += seg.height + 8

chip_row_y = y
for i, name in enumerate(("All", "New", "Star")):
    cls = pd.Chip if i < 2 else pd.Tag
    cls(screen, label=name, x=8 + i * 64, y=chip_row_y, value=(i == 0))

y = chip_row_y + 32
lv = pd.ListView(screen, x=8, y=y, w=screen.width - 40, h=screen.height - y - 8)
for i in range(8):
    pd.Button(lv, label=f"Item {i + 1}", value=i)

screen.visible = True

board_config.runtime.run_forever()
