# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ICON_SIZE
from ..widget import Widget


class Spinner(Widget):
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
        value=0,
        padding=None,
        period_ms=80,
    ):
        """
        Animated circular busy indicator drawn with framebuf arcs.

        Call :meth:`start` / :meth:`stop` to drive the spin via the display task
        list. ``value`` holds the current rotation angle in degrees.
        """
        size = w or h or ICON_SIZE.LARGE
        w = w or size
        h = h or size
        fg = fg if fg is not None else parent.color_theme.primary
        bg = bg if bg is not None else parent.bg
        self.period_ms = period_ms
        self._task = None
        self._running = False
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def start(self):
        """Begin spinning."""
        self._running = True
        self.visible = True
        if self._task is None:
            self._task = self.display.add_task(self._tick, self.period_ms)

    def stop(self):
        """Stop spinning and hide."""
        self._running = False
        self.visible = False
        if self._task is not None:
            try:
                self.display.remove_task(self._task)
            except ValueError:
                pass
            self._task = None

    def _tick(self):
        if not self._running:
            return
        self._value = (int(self._value or 0) + 30) % 360
        self.invalidate()

    def draw(self, _=None):
        """Draw a partial ring whose start angle tracks ``value``."""
        self.parent.draw(self.area)
        pa = self.padded_area
        cx = pa.x + pa.w // 2
        cy = pa.y + pa.h // 2
        r = min(pa.w, pa.h) // 2 - 1
        if r < 2:
            return
        # Track
        self.display.framebuf.circle(cx, cy, r, self.color_theme.outline, f=False)
        a0 = int(self._value or 0)
        a1 = a0 + 120
        self.display.framebuf.arc(cx, cy, r, a0, a1, self.fg)
        # Slightly thicker appearance: second arc one pixel in.
        if r > 3:
            self.display.framebuf.arc(cx, cy, r - 1, a0, a1, self.fg)


# Alias from the plan.
BusyIndicator = Spinner
