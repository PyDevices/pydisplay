"""
widgets_media_busy
====================================================
Showcase :class:`~pdwidgets.Image`, :class:`~pdwidgets.Spinner`,
:class:`~pdwidgets.Toast`, and :class:`~pdwidgets.AppBar`.

A card with an Image placeholder; Load starts a Spinner then shows a Toast.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.background, visible=False)

bar = pd.AppBar(screen, title="Media & busy")
toast = pd.Toast(screen)

card = pd.Card(
    screen,
    w=screen.width - 16,
    h=screen.height - bar.height - 24,
    y=bar.height + 12,
    align=pd.ALIGN.TOP,
    title="Gallery",
)

img = pd.Image(
    card,
    w=min(120, card.width - 24),
    h=min(90, card.height // 3),
    align=pd.ALIGN.TOP,
    y=36,
    value=pd.icon_theme.home(pd.ICON_SIZE.XLARGE),
)

# BusyIndicator is an alias of Spinner — name must appear for coverage.
spinner = pd.BusyIndicator(card, align=pd.ALIGN.CENTER, visible=False)
load_btn = pd.Button(card, label="Load", align=pd.ALIGN.BOTTOM, y=-12, radius=6)

_task = {"t": None, "n": 0}


def _finish():
    spinner.stop()
    # Reveal a larger "loaded" image (reuse home icon at XL).
    img.set_value(pd.icon_theme.info(pd.ICON_SIZE.XLARGE))
    toast.show("Loaded")
    if _task["t"] is not None:
        try:
            display.remove_task(_task["t"])
        except ValueError:
            pass
        _task["t"] = None


def _poll():
    _task["n"] += 1
    if _task["n"] >= 8:  # ~800ms at 100ms period
        _finish()


def do_load(_s=None, _e=None):
    spinner.start()
    _task["n"] = 0
    if _task["t"] is None:
        _task["t"] = display.add_task(_poll, 100)


load_btn.add_event_cb(pd.events.MOUSEBUTTONDOWN, do_load)

screen.visible = True

board_config.runtime.run_forever()
