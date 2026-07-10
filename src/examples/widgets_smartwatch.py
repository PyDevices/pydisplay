# multimer types: all
# pyscript skip: gallery
"""
widgets_smartwatch
====================================================
A smartwatch-style interface built with pdwidgets.

Two "pages" share one ``Screen`` and are swapped by toggling visibility (no
blocking loops, so it behaves under both ``timer_async`` modes):

* **Watch face** — a large ``DigitalClock`` with a date ``Label`` and a row of
  status ``Badge`` dots (battery / Bluetooth) plus an unread-count ``Badge``.
* **Notifications** — a scrollable ``ListView`` of messages with a Back button.

All geometry derives from ``display.width`` / ``display.height`` so the same
example scales from a 240x240 round panel up to 720x720 square displays.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False
pd.init_timer(10)

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.on_background, visible=False)

W, H = screen.width, screen.height
unit = min(W, H)
clock_scale = max(2, unit // 90)
body_scale = max(1, unit // 200)

# ----- Watch face page -----------------------------------------------------
face = pd.Widget(screen, 0, 0, W, H, bg=theme.on_background)

# Status dots along the top, with an unread-count badge.
dot = max(8, unit // 22)
battery = pd.Badge(face, x=unit // 12, y=unit // 12, size=dot, bg=theme.success)  # noqa: F841
bt = pd.Badge(  # noqa: F841
    face, x=unit // 12 + dot + 6, y=unit // 12, size=dot, bg=theme.primary
)
unread = pd.Badge(
    face,
    x=-unit // 12,
    y=unit // 12,
    align=pd.ALIGN.TOP_RIGHT,
    value=3,
    bg=theme.secondary_variant,
)

clock = pd.DigitalClock(
    face,
    align=pd.ALIGN.CENTER,
    y=-unit // 12,
    fg=theme.background,
    bg=theme.on_background,
    scale=clock_scale,
)
date = pd.Label(  # noqa: F841
    face,
    value="Fri Jul 10",
    align=pd.ALIGN.OUTER_BOTTOM,
    align_to=clock,
    y=unit // 20,
    fg=theme.tertiary_variant,
    bg=theme.on_background,
    scale=body_scale,
)

open_notes = pd.Button(
    face,
    label="Messages",
    align=pd.ALIGN.BOTTOM,
    y=-unit // 10,
    radius=unit // 20,
    shadow=2,
)

# ----- Notifications page ---------------------------------------------------
notes = pd.Widget(screen, 0, 0, W, H, bg=theme.background, visible=False)
pd.Label(
    notes,
    value="Notifications",
    align=pd.ALIGN.TOP,
    y=unit // 16,
    fg=theme.on_background,
    bg=theme.background,
    scale=body_scale + 1,
)
back = pd.Button(notes, label="Back", align=pd.ALIGN.TOP_LEFT, x=6, y=6, radius=6)

note_list = pd.ListView(
    notes, w=W - unit // 8, h=H - unit // 4, align=pd.ALIGN.BOTTOM, y=-unit // 16
)
for subject in (
    "Alex: Lunch?",
    "Weather: Rain 3pm",
    "Cal: Standup 9am",
    "Sam: Sent files",
    "Gym: Class 6pm",
):
    item = pd.Button(note_list, label=subject, icon_file=pd.icon_theme.info(pd.ICON_SIZE.SMALL))


def show(page):
    face.visible = page is face
    notes.visible = page is notes


open_notes.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda s, e: show(notes))
back.add_event_cb(pd.events.MOUSEBUTTONDOWN, lambda s, e: show(face))

screen.visible = True

pd.run_forever()
