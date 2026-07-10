# multimer types: all
# pyscript skip: gallery
"""
widgets_settings
====================================================
A settings / preferences screen that exercises the new pdwidgets controls
together: ``Card``, ``Switch``, ``Dropdown``, ``NumberStepper``, ``TextInput``
and a modal ``Dialog``.

Toggles and selections update a status line; the Reset button raises a modal
confirmation ``Dialog``. Runs under both ``timer_async`` modes via
``pd.run_forever()``.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False
pd.init_timer(10)

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

W = screen.width
margin = max(6, W // 40)

header = pd.Widget(
    screen, w=W, h=max(34, screen.height // 12), align=pd.ALIGN.TOP, bg=theme.primary
)
pd.Label(
    header,
    value="Settings",
    align=pd.ALIGN.LEFT,
    x=margin,
    fg=theme.on_primary,
    bg=theme.primary,
    scale=2,
)

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
pd.Label(card, value="Wi-Fi", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)
wifi = pd.Switch(card, x=-pad, y=y - 4, align=pd.ALIGN.TOP_RIGHT, value=True)
wifi.set_change_cb(lambda s: log("Wi-Fi %s" % ("on" if s.value else "off")))

y += 30
pd.Label(card, value="Bluetooth", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)
bt = pd.Switch(card, x=-pad, y=y - 4, align=pd.ALIGN.TOP_RIGHT, value=False)
bt.set_change_cb(lambda s: log("Bluetooth %s" % ("on" if s.value else "off")))

y += 30
pd.Label(card, value="Brightness", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)
bright = pd.NumberStepper(
    card,
    x=-pad,
    y=y - 6,
    w=card.width // 2,
    align=pd.ALIGN.TOP_RIGHT,
    value=70,
    minimum=10,
    maximum=100,
    step=10,
    number_format="{}%",
)
bright.set_change_cb(lambda s: log("Brightness %s" % s.value))

y += 44
name = pd.Label(card, value="Device name", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)  # noqa: F841
y += 18
device = pd.TextInput(card, x=pad, y=y, w=card.width - 2 * pad, value="pixel-watch", max_length=16)
device.set_change_cb(lambda s: log("Name: %s" % s.value))

y += 40
pd.Label(card, value="Theme", x=pad, y=y, align=pd.ALIGN.TOP_LEFT)
theme_dd = pd.Dropdown(
    card,
    x=-pad,
    y=y - 6,
    w=card.width // 2,
    align=pd.ALIGN.TOP_RIGHT,
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

pd.run_forever()
