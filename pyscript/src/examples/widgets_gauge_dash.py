"""
widgets_gauge_dash
====================================================
Showcase :class:`~pdwidgets.Gauge` / :class:`~pdwidgets.Arc`,
:class:`~pdwidgets.FormRow`, :class:`~pdwidgets.Chart`, and
:class:`~pdwidgets.Toast`.

A compact instrument dashboard: gauges driven by a slider; Chart below;
Toast when a threshold is crossed.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

bar = pd.AppBar(screen, title="Gauge dash")
toast = pd.Toast(screen)

size = min(96, screen.width // 3 - 4)
g1 = pd.Gauge(screen, w=size, h=size, x=8, y=bar.height + 12, value=0.3, label="CPU")
g2 = pd.Gauge(
    screen,
    w=size,
    h=size,
    x=8 + size + 8,
    y=bar.height + 12,
    value=0.6,
    fg=theme.secondary_variant,
    label="GPU",
)
g3 = pd.Arc(
    screen,
    w=size,
    h=size,
    x=8 + 2 * (size + 8),
    y=bar.height + 12,
    value=0.2,
    fg=theme.success,
    label="BAT",
)

chart = pd.Chart(
    screen,
    x=8,
    y=bar.height + size + 20,
    w=screen.width - 16,
    h=48,
    mode="line",
    value=[0.3, 0.5, 0.45, 0.7, 0.55, 0.8],
    fg=theme.primary,
)

row = pd.FormRow(
    screen,
    label="Drive",
    y=bar.height + size + 76,
    w=screen.width - 16,
    x=8,
)
slider = pd.Slider(row, value=0.3, w=screen.width // 2, step=0.05)

_warned = {"v": False}
_hist = [0.3, 0.5, 0.45, 0.7, 0.55, 0.8]


def on_slide(s):
    v = s.value
    g1.set_value(v)
    g2.set_value(min(1.0, v + 0.2))
    g3.set_value(max(0.0, 1.0 - v))
    _hist.pop(0)
    _hist.append(v)
    chart.value = list(_hist)
    if v >= 0.85 and not _warned["v"]:
        toast.show("High load")
        _warned["v"] = True
    elif v < 0.7:
        _warned["v"] = False


slider.set_change_cb(on_slide)

screen.visible = True

board_config.runtime.run_forever()
