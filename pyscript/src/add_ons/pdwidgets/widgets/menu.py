# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Menu / ContextMenu — popup action list (labels → callbacks)."""

from eventsys import events

from .._constants import ALIGN, PAD, TEXT_SIZE, TEXT_WIDTH
from .._util import _root_screen
from ..widget import Widget
from .button import Button
from .card import Card


class Menu(Widget):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        items=None,
        x=0,
        y=0,
        w=None,
        h=None,
        fg=None,
        bg=None,
        scrim=None,
    ):
        """
        Popup action menu. ``items`` is a sequence of ``(label, callback)``.

        Unlike :class:`Dropdown`, this does not hold an option value — each row
        fires its callback and closes.
        """
        screen = _root_screen(parent)
        display = parent.display
        self.scrim = scrim if scrim is not None else parent.color_theme.sheet_scrim
        bg = bg if bg is not None else parent.color_theme.menu_surface
        fg = fg if fg is not None else parent.color_theme.on_menu
        self._items = list(items or [])
        super().__init__(
            screen, 0, 0, display.width, display.height, fg=fg, bg=None, visible=False
        )
        row_h = TEXT_SIZE.LARGE + 2 * PAD
        n = max(1, len(self._items))
        card_w = w or min(
            display.width - 2 * PAD,
            max(len(lbl) for lbl, _ in self._items or [("Menu", None)]) * TEXT_WIDTH + 4 * PAD,
        )
        card_h = h or n * row_h + 2 * PAD
        self.card = Card(
            self,
            w=card_w,
            h=card_h,
            x=x,
            y=y,
            align=ALIGN.TOP_LEFT if (x or y) else ALIGN.CENTER,
            fg=fg,
            bg=bg,
            shadow=3,
        )
        for i, (label, cb) in enumerate(self._items):
            btn = Button(
                self.card,
                label=label,
                w=card_w - 2 * PAD,
                x=PAD,
                y=PAD + i * row_h,
                align=ALIGN.TOP_LEFT,
                bg=bg,
                text_color=fg,
                radius=4,
            )
            btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_action(cb))

    def _make_action(self, callback):
        def handler(data=None, event=None):
            self.hide_menu()
            if callback:
                callback()

        return handler

    def show(self):
        self.visible = True
        self.set_modal(True)
        self.invalidate()

    def hide_menu(self):
        self.set_modal(False)
        self.visible = False

    def draw(self, area=None):
        area = area or self.area
        self.display.framebuf.fill_rect(*area, self.scrim)


ContextMenu = Menu
