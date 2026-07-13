# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""ScrollView — generic scroll container with clip + drag/wheel."""

from eventsys import events

from .._constants import ALIGN
from ..widget import Widget
from .scroll_bar import ScrollBar


class ScrollView(Widget):
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
        padding=None,
        content_h=None,
    ):
        """
        Scrollable viewport. Children are offset by ``scroll_y``; drawing is
        clipped to the padded area (Phase 0 ``clip_content``).
        """
        fg = fg if fg is not None else parent.color_theme.on_surface
        bg = bg if bg is not None else parent.color_theme.surface
        super().__init__(
            parent, x, y, w, h, align, align_to, fg, bg, visible, value=0, padding=padding
        )
        self.clip_content = True
        self._scroll_y = 0
        self._content_h = content_h or (h or parent.height)
        self._drag_y = None
        self.scrollbar = ScrollBar(
            parent,
            vertical=True,
            h=h,
            fg=fg,
            bg=bg,
            visible=False,
            align_to=self,
            align=ALIGN.OUTER_RIGHT,
        )
        self.scrollbar.slider.set_change_cb(self._on_scrollbar)

    @property
    def scroll_y(self):
        return self._scroll_y

    @scroll_y.setter
    def scroll_y(self, y):
        max_y = max(0, self._content_h - self.height)
        y = max(0, min(int(y), max_y))
        if y == self._scroll_y:
            return
        dy = y - self._scroll_y
        self._scroll_y = y
        for child in self.children:
            child.set_position(y=child._y - dy)
        self._sync_scrollbar()
        self.invalidate()

    def set_content_height(self, h):
        self._content_h = max(int(h), self.height)
        self._sync_scrollbar()

    def add_child(self, child):
        super().add_child(child)
        bottom = (child._y or 0) + child.height
        self._content_h = max(self._content_h, bottom)
        self._sync_scrollbar()

    def _sync_scrollbar(self):
        overflow = self._content_h > self.height
        self.scrollbar.visible = overflow
        if overflow:
            self.scrollbar.slider.value = self._scroll_y / (self._content_h - self.height)

    def _on_scrollbar(self, sender):
        max_y = max(0, self._content_h - self.height)
        self.scroll_y = int(sender.value * max_y)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._drag_start)
        self.add_event_cb(events.MOUSEMOTION, self._drag_move)
        self.add_event_cb(events.MOUSEBUTTONUP, self._drag_end)
        self.add_event_cb(events.MOUSEWHEEL, self._wheel)

    def _drag_start(self, data=None, event=None):
        self._drag_y = event.pos[1]

    def _drag_move(self, data=None, event=None):
        if self._drag_y is None:
            return
        dy = self._drag_y - event.pos[1]
        self._drag_y = event.pos[1]
        if dy:
            self.scroll_y = self._scroll_y + dy

    def _drag_end(self, data=None, event=None):
        self._drag_y = None

    def _wheel(self, data=None, event=None):
        y = getattr(event, "y", 0) or 0
        self.scroll_y = self._scroll_y - int(y) * 16

    def draw(self, area=None):
        if self.bg is not None:
            self.display.framebuf.fill_rect(*(area or self.area), self.bg)
