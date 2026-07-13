# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""BottomSheet — modal slide-up panel + scrim."""

from eventsys import events

from .._constants import ALIGN, PAD
from .._util import _root_screen
from ..widget import Widget
from .card import Card


class BottomSheet(Widget):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        title=None,
        h=None,
        fg=None,
        bg=None,
        scrim=None,
        on_dismiss=None,
    ):
        """Modal panel anchored to the bottom of the screen."""
        screen = _root_screen(parent)
        display = parent.display
        self.scrim = scrim if scrim is not None else parent.color_theme.sheet_scrim
        self.on_dismiss = on_dismiss
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        super().__init__(
            screen, 0, 0, display.width, display.height, fg=fg, bg=None, visible=False
        )
        sheet_h = h or display.height // 2
        self.panel = Card(
            self,
            w=display.width,
            h=sheet_h,
            align=ALIGN.BOTTOM,
            fg=fg,
            bg=bg,
            title=title,
            shadow=4,
        )
        self.clip_content = False
        # Tap scrim (outside panel) to dismiss
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._scrim_tap)

    @property
    def content(self):
        """Attach children to the panel card."""
        return self.panel

    def _scrim_tap(self, data=None, event=None):
        pt = self.display.translate_point(event.pos)
        if not self.panel.area.contains(*pt):
            self.hide_sheet()

    def show(self):
        self.visible = True
        self.set_modal(True)
        self.invalidate()

    def hide_sheet(self):
        self.set_modal(False)
        self.visible = False
        if self.on_dismiss:
            self.on_dismiss()

    def draw(self, area=None):
        area = area or self.area
        self.display.framebuf.fill_rect(*area, self.scrim)
