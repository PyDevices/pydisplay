# pyscript mip: pdwidgets
# pyodide wheels: pdwidgets
# pyscript skip: binaries
"""
widgets_smartwatch
====================================================
A smartwatch-style interface built with pdwidgets.

Two :class:`~pdwidgets.Page` children share a :class:`~pdwidgets.Navigator`
(no blocking loops, so it behaves under both ``timer_async`` modes):

* **Watch face** — a large ``DigitalClock`` with a date ``Label`` and a row of
  status ``Badge`` dots (battery / Bluetooth) plus an unread-count ``Badge``.
* **Notifications** — a scrollable ``ListView`` of messages with AppBar back.

All geometry derives from ``display.width`` / ``display.height`` so the same
example scales from a 240x240 round panel up to 720x720 square displays.
"""

import board_config
import pdwidgets as pd

pd.DEBUG = False
pd.MARK_UPDATES = False

display = pd.Display(board_config.display_drv, board_config.runtime)
theme = display.color_theme
screen = pd.Screen(display, bg=theme.on_background, visible=False)

W, H = screen.width, screen.height
unit = min(W, H)
clock_scale = max(2, unit // 90)
body_scale = max(1, unit // 200)

nav = pd.Navigator(screen)

# ----- Watch face page -----------------------------------------------------
face = pd.Page(nav, title="Face", bg=theme.on_background)

dot = max(8, unit // 22)
battery = pd.Badge(face, x=unit // 12, y=unit // 12, size=dot, bg=theme.success)  # noqa: F841
bt = pd.Badge(  # noqa: F841
    face, x=unit // 12 + dot + 6, y=unit // 12, size=dot, bg=theme.primary
)
unread = pd.Badge(  # noqa: F841
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
notes = pd.Page(nav, title="Notifications", bg=theme.background, visible=False)


def go_face(_=None):
    nav.pop()


notes_bar = pd.AppBar(notes, title="Notifications", on_back=go_face)

note_list = pd.ListView(
    notes,
    w=W - unit // 8,
    h=H - unit // 4 - notes_bar.height,
    align=pd.ALIGN.BOTTOM,
    y=-unit // 16,
)
for subject in (
    "Alex: Lunch?",
    "Weather: Rain 3pm",
    "Cal: Standup 9am",
    "Sam: Sent files",
    "Gym: Class 6pm",
):
    pd.Button(note_list, label=subject, icon_file=pd.icon_theme.info(pd.ICON_SIZE.SMALL))


def open_notes_page(_s=None, _e=None):
    nav.push(notes)


open_notes.add_event_cb(pd.events.MOUSEBUTTONDOWN, open_notes_page)

nav.push(face)
screen.visible = True

board_config.runtime.run_forever()
