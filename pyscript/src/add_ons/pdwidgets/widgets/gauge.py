# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ICON_SIZE, TEXT_SIZE
from ..widget import Widget


class Gauge(Widget):
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
        value=0.0,
        padding=None,
        start_angle=135,
        sweep=270,
        track_color=None,
        label=None,
    ):
        """
        Arc / dial gauge for a normalized ``value`` in ``[0, 1]``.

        Draws a background track arc and a value arc. Optional center ``label``
        (string) is drawn with the romfont when set.

        ``Arc`` is an alias of this class.
        """
        size = w or h or ICON_SIZE.XLARGE * 2
        w = w or size
        h = h or size
        fg = fg if fg is not None else parent.color_theme.primary
        bg = bg if bg is not None else parent.bg
        self.start_angle = start_angle
        self.sweep = sweep
        self.track_color = track_color if track_color is not None else parent.color_theme.outline
        self.label = label
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def draw(self, _=None):
        """Draw track + value arcs and optional center text."""
        self.parent.draw(self.area)
        pa = self.padded_area
        cx = pa.x + pa.w // 2
        cy = pa.y + pa.h // 2
        r = min(pa.w, pa.h) // 2 - 1
        if r < 3:
            return
        a0 = self.start_angle
        a1 = self.start_angle + self.sweep
        self.display.framebuf.arc(cx, cy, r, a0, a1, self.track_color)
        if r > 4:
            self.display.framebuf.arc(cx, cy, r - 1, a0, a1, self.track_color)
        v = self._value if self._value is not None else 0.0
        if v < 0:
            v = 0.0
        elif v > 1:
            v = 1.0
        if v > 0:
            ve = a0 + int(self.sweep * v)
            self.display.framebuf.arc(cx, cy, r, a0, ve, self.fg)
            if r > 4:
                self.display.framebuf.arc(cx, cy, r - 1, a0, ve, self.fg)
        text = self.label
        if text is None:
            text = "%d%%" % int(v * 100)
        th = TEXT_SIZE.MEDIUM
        tw = len(text) * 8
        self.display.framebuf.text(
            text, cx - tw // 2, cy - th // 2, self.color_theme.on_surface, height=th
        )


Arc = Gauge
