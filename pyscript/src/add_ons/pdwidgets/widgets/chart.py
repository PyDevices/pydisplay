# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Chart — tiny line / bar chart (MCU-light)."""

from .._constants import PAD
from ..widget import Widget


class Chart(Widget):
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
        mode="line",
        auto_scale=True,
    ):
        """
        Plot ``value`` as a sequence of numbers.

        ``mode`` is ``\"line\"`` or ``\"bar\"``. Values in ``[0, 1]`` plot
        directly; otherwise ``auto_scale`` maps min..max into the plot area.
        """
        self.mode = mode
        self.auto_scale = auto_scale
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.primary
        value = list(value) if value is not None else [0.2, 0.5, 0.4, 0.8, 0.6]
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def _normalized(self):
        data = list(self._value or [])
        if not data:
            return []
        if self.auto_scale:
            lo = min(data)
            hi = max(data)
            if hi <= lo:
                return [0.5] * len(data)
            if lo >= 0 and hi <= 1:
                return [max(0.0, min(1.0, float(v))) for v in data]
            return [(float(v) - lo) / (hi - lo) for v in data]
        return [max(0.0, min(1.0, float(v))) for v in data]

    def draw(self, _=None):
        pa = self.padded_area
        self.display.framebuf.fill_rect(*pa, self.bg)
        self.display.framebuf.rect(pa.x, pa.y, pa.w, pa.h, self.color_theme.outline)
        data = self._normalized()
        if not data:
            return
        n = len(data)
        plot_h = pa.h - 2
        plot_y = pa.y + 1
        if self.mode == "bar":
            gap = 1
            bar_w = max(1, (pa.w - 2 - gap * (n - 1)) // n)
            for i, v in enumerate(data):
                bh = max(1, int(v * plot_h))
                x = pa.x + 1 + i * (bar_w + gap)
                self.display.framebuf.fill_rect(x, plot_y + plot_h - bh, bar_w, bh, self.fg)
        else:
            if n == 1:
                y = plot_y + plot_h - int(data[0] * plot_h)
                self.display.framebuf.fill_rect(pa.x + pa.w // 2, y, 2, 2, self.fg)
                return
            pts = []
            for i, v in enumerate(data):
                x = pa.x + 1 + int(i * (pa.w - 3) / (n - 1))
                y = plot_y + plot_h - int(v * plot_h)
                pts.append((x, y))
            for i in range(len(pts) - 1):
                x0, y0 = pts[i]
                x1, y1 = pts[i + 1]
                self.display.framebuf.line(x0, y0, x1, y1, self.fg)
