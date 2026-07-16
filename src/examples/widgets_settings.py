# deps: pdwidgets
"""
widgets_settings
====================================================
A settings / preferences screen that exercises pdwidgets controls together:
``AppBar``, ``Card``, ``FormRow``, ``Divider``, ``Switch``, ``Dropdown``,
``NumberStepper``, ``TextInput`` and a modal ``Dialog``.

Toggles and selections update a status line; the Reset button raises a modal
confirmation ``Dialog``. Runs under both ``timer_async`` modes via
``runtime.run_forever()``.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

W = screen.width
margin = max(6, W // 40)

header = pd.AppBar(screen, title="Settings")

status = pd.TextBox(
    screen,
    w=W,
    align=pd.ALIGN.BOTTOM,
    scale=1,
    fg=theme.on_surface,
    bg=theme.surface_variant,
    value="Preferences",
)


def log(msg):
    status.set_value(msg)


card = pd.Card(
    screen,
    w=W - 2 * margin,
    h=status.y - header.height - 2 * margin,
    y=header.height + margin,
    align=pd.ALIGN.TOP,
)
pad = margin + 4

y = margin
row = pd.FormRow(card, label="Wi-Fi", x=pad, y=y, w=card.width - 2 * pad)
wifi = pd.Switch(row, value=True)
wifi.set_change_cb(lambda s: log("Wi-Fi %s" % ("on" if s.value else "off")))

y += row.height + 2
pd.Divider(card, x=pad, y=y, w=card.width - 2 * pad)

y += 10
row = pd.FormRow(card, label="Bluetooth", x=pad, y=y, w=card.width - 2 * pad)
bt = pd.Switch(row, value=False)
bt.set_change_cb(lambda s: log("Bluetooth %s" % ("on" if s.value else "off")))

y += row.height + 2
pd.Divider(card, x=pad, y=y, w=card.width - 2 * pad)

y += 10
row = pd.FormRow(card, label="Brightness", x=pad, y=y, w=card.width - 2 * pad)
bright = pd.NumberStepper(
    row,
    w=card.width // 2,
    value=70,
    minimum=10,
    maximum=100,
    step=10,
    number_format="{}%",
)
bright.set_change_cb(lambda s: log("Brightness %s" % s.value))

y += row.height + 2
pd.Divider(card, x=pad, y=y, w=card.width - 2 * pad)

y += 10
pd.Label(card, value="Device name", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)
y += 18
device = pd.TextInput(card, x=pad, y=y, w=card.width - 2 * pad, value="pixel-watch", max_length=16)
device.set_change_cb(lambda s: log("Name: %s" % s.value))

y += 40
row = pd.FormRow(card, label="Theme", x=pad, y=y, w=card.width - 2 * pad)
theme_dd = pd.Dropdown(
    row,
    w=card.width // 2,
    options=["Light", "Dark", "Auto"],
)
theme_dd.set_change_cb(lambda s: log("Theme: %s" % s.value))

reset = pd.Button(
    card,
    label="Reset",
    align=pd.ALIGN.BOTTOM,
    y=-pad,
    radius=6,
    shadow=2,
    bg=theme.error,
    text_color=theme.on_error,
)
confirm = pd.Dialog(
    screen,
    "Reset all settings?",
    title="Reset",
    buttons=["Cancel", "Reset"],
    on_result=lambda label: log("Settings reset." if label == "Reset" else "Cancelled."),
)
reset.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda s, e: confirm.show())

screen.visible = True

board_config.runtime.run_forever()
