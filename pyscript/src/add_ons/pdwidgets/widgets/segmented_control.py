# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""SegmentedControl — exclusive pill buttons."""

from eventsys import events

from .._constants import PAD, TEXT_SIZE, TEXT_WIDTH
from ..widget import Widget


class SegmentedControl(Widget):
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
        labels=None,
        text_height=TEXT_SIZE.MEDIUM,
        radius=8,
    ):
        """Exclusive segments; ``value`` is the selected index."""
        self.labels = list(labels or ["A", "B"])
        self.text_height = text_height
        self.radius = radius
        n = len(self.labels)
        w = w or (sum(len(s) for s in self.labels) * TEXT_WIDTH + n * 4 * PAD)
        h = h or text_height + 2 * PAD
        bg = bg if bg is not None else parent.color_theme.segment
        fg = fg if fg is not None else parent.color_theme.on_segment
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._tap)

    def _tap(self, data=None, event=None):
        pa = self.padded_area
        n = len(self.labels) or 1
        seg_w = pa.w // n
        px = self.display.translate_point(event.pos)[0]
        idx = max(0, min(n - 1, (px - pa.x) // seg_w))
        self.value = idx

    def draw(self, _=None):
        pa = self.padded_area
        self.display.framebuf.round_rect(*pa, self.radius, self.color_theme.segment, f=True)
        n = len(self.labels) or 1
        seg_w = pa.w // n
        for i, label in enumerate(self.labels):
            x = pa.x + i * seg_w
            selected = i == self._value
            fill = self.color_theme.segment_selected if selected else self.color_theme.segment
            ink = self.color_theme.on_segment_selected if selected else self.color_theme.on_segment
            self.display.framebuf.fill_rect(x, pa.y, seg_w, pa.h, fill)
            tw = len(label) * TEXT_WIDTH
            tx = x + (seg_w - tw) // 2
            ty = pa.y + (pa.h - self.text_height) // 2
            self.display.framebuf.text(label, tx, ty, ink, height=self.text_height)
        self.display.framebuf.round_rect(*pa, self.radius, self.color_theme.outline, f=False)
