# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""DatePicker — month calendar grid; value is (y, m, d) or ISO string."""

from eventsys import events

from .._constants import PAD, TEXT_SIZE, TEXT_WIDTH
from ..widget import Widget
from .button import Button
from .label import Label

_DAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")


def _days_in_month(y, m):
    if m == 2:
        leap = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
        return 29 if leap else 28
    if m in (4, 6, 9, 11):
        return 30
    return 31


def _weekday(y, m, d):
    """Monday=0 … Sunday=6 (simple Sakamoto)."""
    t = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
    y -= m < 3
    return (y + y // 4 - y // 100 + y // 400 + t[m - 1] + d) % 7


class DatePicker(Widget):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
        weekdays=None,
    ):
        """
        Month calendar. ``value`` is ``(y, m, d)`` or ``\"YYYY-MM-DD\"``.
        ``weekdays`` may override the short English labels.
        """
        self.weekdays = list(weekdays) if weekdays else list(_DAYS)
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        w = w or min(parent.width, 200)
        h = h or 160
        if value is None:
            value = (2026, 7, 13)
        elif isinstance(value, str):
            parts = value.split("-")
            value = (int(parts[0]), int(parts[1]), int(parts[2]))
        self._year, self._month, self._day = value
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self._title = Label(
            self,
            value=self._title_text(),
            x=PAD * 4,
            y=2,
            fg=fg,
            bg=bg,
            text_height=TEXT_SIZE.MEDIUM,
        )
        self._prev = Button(
            self,
            label="<",
            w=TEXT_SIZE.LARGE + PAD,
            h=TEXT_SIZE.LARGE + PAD,
            x=2,
            y=0,
            bg=self.color_theme.surface_variant,
            text_color=fg,
            radius=4,
        )
        self._next = Button(
            self,
            label=">",
            w=TEXT_SIZE.LARGE + PAD,
            h=TEXT_SIZE.LARGE + PAD,
            x=self.width - TEXT_SIZE.LARGE - PAD - 2,
            y=0,
            bg=self.color_theme.surface_variant,
            text_color=fg,
            radius=4,
        )
        self._prev.add_event_cb(events.MOUSEBUTTONDOWN, self._go_prev)
        self._next.add_event_cb(events.MOUSEBUTTONDOWN, self._go_next)
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._tap_day)

    def _title_text(self):
        return f"{self._year}-{self._month:02d}"

    def _go_prev(self, data=None, event=None):
        self._month -= 1
        if self._month < 1:
            self._month = 12
            self._year -= 1
        self._title.value = self._title_text()
        self.invalidate()

    def _go_next(self, data=None, event=None):
        self._month += 1
        if self._month > 12:
            self._month = 1
            self._year += 1
        self._title.value = self._title_text()
        self.invalidate()

    def _cell_grid(self):
        pa = self.padded_area
        header = TEXT_SIZE.LARGE + 2 * PAD
        top = pa.y + header
        cell_w = pa.w // 7
        cell_h = (pa.h - header) // 7
        return top, cell_w, cell_h, pa.x

    def _tap_day(self, data=None, event=None):
        px, py = self.display.translate_point(event.pos)
        top, cell_w, cell_h, left = self._cell_grid()
        if py < top + cell_h:
            return  # weekday row
        col = (px - left) // cell_w
        row = (py - top) // cell_h - 1
        if col < 0 or col > 6 or row < 0:
            return
        first = _weekday(self._year, self._month, 1)
        # Convert Sunday=0 Sakamoto… wait we used Monday=0? Sakamoto returns Sun=0
        # Adjust: Python docs Sakamoto: 0=Sunday. Convert to Mon=0:
        first_mon = (first + 6) % 7
        day = row * 7 + col - first_mon + 1
        dim = _days_in_month(self._year, self._month)
        if 1 <= day <= dim:
            self._day = day
            self.value = (self._year, self._month, self._day)

    def draw(self, _=None):
        pa = self.padded_area
        self.display.framebuf.fill_rect(*pa, self.bg)
        top, cell_w, cell_h, left = self._cell_grid()
        for i, name in enumerate(self.weekdays):
            tx = left + i * cell_w + 2
            self.display.framebuf.text(
                name, tx, top + 2, self.color_theme.tertiary, height=TEXT_SIZE.SMALL
            )
        first = _weekday(self._year, self._month, 1)
        first_mon = (first + 6) % 7
        dim = _days_in_month(self._year, self._month)
        for day in range(1, dim + 1):
            idx = first_mon + day - 1
            row, col = divmod(idx, 7)
            x = left + col * cell_w
            y = top + (row + 1) * cell_h
            selected = day == self._day
            if selected:
                self.display.framebuf.fill_rect(
                    x + 1, y + 1, cell_w - 2, cell_h - 2, self.color_theme.primary
                )
                ink = self.color_theme.on_primary
            else:
                ink = self.fg
            label = str(day)
            tx = x + (cell_w - len(label) * TEXT_WIDTH) // 2
            ty = y + (cell_h - TEXT_SIZE.MEDIUM) // 2
            self.display.framebuf.text(label, tx, ty, ink, height=TEXT_SIZE.MEDIUM)
