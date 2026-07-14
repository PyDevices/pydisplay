# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Accordion / ExpansionPanel — header + expandable body."""

from eventsys import events

from .._constants import ALIGN, PAD, TEXT_SIZE, TEXT_WIDTH
from ..widget import Widget
from .button import Button


class Accordion(Widget):
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
        exclusive=True,
    ):
        """Stack of expansion panels; ``exclusive`` keeps at most one open."""
        self.exclusive = exclusive
        self._panels = []
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def add_panel(self, title, body: Widget, open_=False):
        """Add a titled panel wrapping ``body``; returns the header button."""
        header = Button(
            self,
            label=title,
            w=self.width,
            h=TEXT_SIZE.LARGE + 2 * PAD,
            bg=self.color_theme.surface_variant,
            text_color=self.color_theme.on_surface,
            radius=4,
        )
        body.parent = self
        body.visible = open_
        panel = {"title": title, "header": header, "body": body, "open": open_}
        self._panels.append(panel)
        header.add_event_cb(events.MOUSEBUTTONDOWN, self._make_toggle(panel))
        self._relayout()
        return header

    def _make_toggle(self, panel):
        def cb(data=None, event=None):
            opening = not panel["open"]
            if opening and self.exclusive:
                for p in self._panels:
                    if p is not panel and p["open"]:
                        p["open"] = False
                        p["body"].visible = False
            panel["open"] = opening
            panel["body"].visible = opening
            self._relayout()
            self.invalidate()

        return cb

    def _relayout(self):
        y = 0
        for p in self._panels:
            p["header"].set_position(x=0, y=y, w=self.width, align=ALIGN.TOP_LEFT, align_to=self)
            y += p["header"].height + 2
            if p["open"]:
                p["body"].set_position(
                    x=PAD, y=y, w=self.width - 2 * PAD, align=ALIGN.TOP_LEFT, align_to=self
                )
                y += p["body"].height + PAD


ExpansionPanel = Accordion
