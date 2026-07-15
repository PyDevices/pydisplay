# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
"""
widgets_sheets
====================================================
Showcase :class:`~pdwidgets.Drawer`, :class:`~pdwidgets.BottomSheet`,
:class:`~pdwidgets.Accordion` / :class:`~pdwidgets.ExpansionPanel`,
:class:`~pdwidgets.ScrollView`, :class:`~pdwidgets.Grid`,
:class:`~pdwidgets.PasswordField`, :class:`~pdwidgets.PinPad`, and
:class:`~pdwidgets.Form`.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

toast = pd.Toast(screen)
bar = pd.AppBar(screen, title="Sheets")

drawer = pd.Drawer(screen, title="Drawer")
pd.Label(drawer.content, value="Side menu", y=36, x=8)
sheet = pd.BottomSheet(screen, title="Sheet", h=screen.height // 2)
pd.Label(sheet.content, value="Bottom content", y=36, x=8)


def show_drawer(_=None, event=None):
    drawer.show()


def show_sheet(_=None, event=None):
    sheet.show()


pd.Button(screen, label="Drawer", x=8, y=bar.height + 8, w=70, h=28).add_event_cb(
    pd.events.MOUSEBUTTONDOWN, show_drawer
)
pd.Button(screen, label="Sheet", x=86, y=bar.height + 8, w=70, h=28).add_event_cb(
    pd.events.MOUSEBUTTONDOWN, show_sheet
)

# Accordion (+ ExpansionPanel alias)
acc = pd.Accordion(screen, x=8, y=bar.height + 44, w=screen.width - 16, h=90)
body1 = pd.Label(screen, value="Section A body", visible=False, w=100, h=20)
body2 = pd.Label(screen, value="Section B body", visible=False, w=100, h=20)
acc.add_panel("Section A", body1, open_=True)
acc.add_panel("Section B", body2)
_ = pd.ExpansionPanel

# ScrollView with overflowing labels
sv = pd.ScrollView(
    screen,
    x=8,
    y=bar.height + 140,
    w=screen.width // 2 - 12,
    h=80,
    content_h=200,
)
for i in range(6):
    pd.Label(sv, value=f"Scroll line {i}", y=i * 22, x=4, w=sv.width - 8, h=20)

# Grid of actions
grid = pd.Grid(screen, x=screen.width // 2 + 4, y=bar.height + 140, w=screen.width // 2 - 12, h=80, columns=2)
for label in ("A", "B", "C", "D"):
    pd.Button(grid, label=label, h=28)

# Form binder + PasswordField + PinPad
err = pd.Label(screen, value="", y=screen.height - 18, x=8, w=screen.width - 16, h=16, fg=theme.error)
pwd = pd.PasswordField(screen, hint="PIN", x=8, y=screen.height - 120, w=120, h=28, max_length=6)


def _require_pin(v):
    return None if len(v or "") >= 4 else "PIN too short"


form = pd.Form(on_commit=lambda vals: toast.show("OK"), error_label=err)
form.add("pin", pwd, validator=_require_pin)

pad = pd.PinPad(
    screen,
    x=140,
    y=screen.height - 120,
    w=screen.width - 148,
    h=100,
    target=pwd,
    on_enter=lambda _v: form.commit() or toast.show("Locked"),
)

screen.visible = True

board_config.runtime.run_forever()
