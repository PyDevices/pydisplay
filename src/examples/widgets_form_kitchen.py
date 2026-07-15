# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
# pyscript skip: binaries
"""
widgets_form_kitchen
====================================================
Showcase :class:`~pdwidgets.FormRow`, :class:`~pdwidgets.Divider`,
:class:`~pdwidgets.AppBar`, :class:`~pdwidgets.Toast`, and
:class:`~pdwidgets.Keyboard`.

A preferences form laid out with FormRows; Save shows a Toast. Focusing the
device-name field shows the on-screen Keyboard.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

bar = pd.AppBar(screen, title="Form kitchen")
toast = pd.Toast(screen)
keyboard = pd.Keyboard(screen, visible=False)

card = pd.Card(
    screen,
    w=screen.width - 12,
    h=screen.height - bar.height - 16,
    y=bar.height + 8,
    align=pd.ALIGN.TOP,
    title="Preferences",
)

y = 28
# ListTile is an alias of FormRow — name must appear for coverage.
row_wifi = pd.ListTile(card, label="Wi-Fi", y=y, w=card.width - 8, x=4)
wifi = pd.Switch(row_wifi, value=True)

y += row_wifi.height + 4
pd.Divider(card, y=y, w=card.width - 16, x=8)

y += 10
row_bright = pd.FormRow(card, label="Brightness", y=y, w=card.width - 8, x=4)
bright = pd.NumberStepper(row_bright, value=5, minimum=0, maximum=10, w=card.width // 2)

y += row_bright.height + 4
pd.Divider(card, y=y, w=card.width - 16, x=8)

y += 10
row_theme = pd.FormRow(card, label="Theme", y=y, w=card.width - 8, x=4)
theme_dd = pd.Dropdown(row_theme, options=["Auto", "Day", "Night"], value="Auto", w=100)

y += row_theme.height + 4
pd.Divider(card, y=y, w=card.width - 16, x=8)

y += 10
pd.Label(card, value="Device name", x=8, y=y, align=pd.ALIGN.TOP_LEFT)
y += 20
name = pd.TextInput(card, x=8, y=y, w=card.width - 16, value="pixel-watch", max_length=16)


def on_focus(_s=None, _e=None):
    keyboard.show(target=name)


name.add_event_cb(pd.events.MOUSEBUTTONDOWN, on_focus)

y += name.height + 12
save = pd.Button(card, label="Save", y=y, align=pd.ALIGN.TOP, radius=6)


def do_save(_s=None, _e=None):
    keyboard.hide_keyboard()
    toast.show("Saved %s" % (name.value or ""))


save.add_event_cb(pd.events.MOUSEBUTTONDOWN, do_save)

wifi.set_change_cb(lambda s: toast.show("Wi-Fi %s" % ("on" if s.value else "off")))

screen.visible = True

board_config.runtime.run_forever()
