# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
"""
widgets_pickers
====================================================
Showcase :class:`~pdwidgets.ColorPicker` and :class:`~pdwidgets.DatePicker`.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

toast = pd.Toast(screen)
bar = pd.AppBar(screen, title="Pickers")

swatch = pd.TextBox(
    screen,
    value="color",
    x=8,
    y=bar.height + 8,
    w=80,
    h=28,
    bg=theme.primary,
    fg=theme.on_primary,
)

picker = pd.ColorPicker(screen, x=8, y=bar.height + 44, w=min(160, screen.width - 16), h=100)


def on_color(w):
    swatch.bg = w.value
    swatch.invalidate()


picker.set_change_cb(on_color)

date_lbl = pd.TextBox(
    screen,
    value="2026-07-13",
    x=8,
    y=bar.height + 156,
    w=120,
    h=24,
)

dp = pd.DatePicker(screen, x=8, y=bar.height + 186, w=min(200, screen.width - 16), h=140, value=(2026, 7, 13))


def on_date(w):
    y, m, d = w.value
    date_lbl.value = f"{y:04d}-{m:02d}-{d:02d}"
    toast.show(date_lbl.value)


dp.set_change_cb(on_date)

screen.visible = True

board_config.runtime.run_forever()
