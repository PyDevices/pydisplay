# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from .._constants import ALIGN, ICON_SIZE, PAD, TEXT_SIZE, TEXT_WIDTH
from ..widget import Widget
from .button import Button
from .page import Page


class TabView(Widget):
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
        tabs=None,
        bar_height=None,
    ):
        """
        Tab bar plus a content area hosting one :class:`Page` per tab.

        Args:
            tabs (list): Sequence of ``(label, Page)`` or just labels (empty
                pages are created). Example::

                    tabs = [("Home", home_page), ("Log", log_page)]
                    tv = TabView(screen, tabs=tabs)

            value (int): Initially selected tab index.
        """
        w = w or parent.width
        h = h or parent.height
        bg = bg if bg is not None else parent.bg
        fg = fg if fg is not None else parent.fg
        self.bar_height = bar_height or (ICON_SIZE.LARGE + PAD)
        super().__init__(
            parent,
            x,
            y,
            w,
            h,
            align,
            align_to,
            fg,
            bg,
            visible,
            value,
            padding or (0, 0, 0, 0),
        )
        self._pages = []
        self._buttons = []
        self.tab_bar = Widget(
            self,
            w=w,
            h=self.bar_height,
            align=ALIGN.TOP,
            bg=self.color_theme.surface_variant,
            fg=fg,
            padding=(0, 0, 0, 0),
        )
        self.content = Widget(
            self,
            y=self.bar_height,
            w=w,
            h=h - self.bar_height,
            align=ALIGN.TOP_LEFT,
            bg=bg,
            fg=fg,
            padding=(0, 0, 0, 0),
        )
        self._build_tabs(tabs or [])
        self.set_index(int(value) if value else 0)

    def _build_tabs(self, tabs):
        n = len(tabs) or 1
        btn_w = self.width // n
        for i, item in enumerate(tabs):
            if isinstance(item, (tuple, list)):
                label, page = item[0], item[1]
            else:
                label, page = item, None
            if page is None:
                page = Page(self.content, visible=False)
            elif page.parent is not self.content:
                page.parent = self.content
                page.set_position(w=self.content.width, h=self.content.height)
            page.visible = False
            self._pages.append(page)
            btn = Button(
                self.tab_bar,
                w=btn_w,
                h=self.bar_height,
                x=i * btn_w,
                align=ALIGN.TOP_LEFT,
                label=label,
                radius=0,
                text_height=TEXT_SIZE.MEDIUM,
                bg=self.color_theme.surface_variant,
                text_color=self.color_theme.on_surface,
            )
            # Shrink label auto-width was wrong when w fixed — Button may still
            # have created a label; ensure we keep the given width.
            btn.set_position(w=btn_w, h=self.bar_height, x=i * btn_w)
            idx = i

            def make_cb(index):
                def _cb(data=None, event=None):
                    self.set_index(index)

                return _cb

            btn.add_event_cb(events.MOUSEBUTTONDOWN, make_cb(idx))
            self._buttons.append(btn)

    def set_index(self, index):
        """Select the tab at ``index`` and show its page."""
        if not self._pages:
            return
        index = max(0, min(index, len(self._pages) - 1))
        self._value = index
        for i, page in enumerate(self._pages):
            page.visible = i == index
            btn = self._buttons[i]
            if i == index:
                btn.bg = self.color_theme.primary
                if hasattr(btn, "label") and btn.label:
                    btn.label.fg = self.color_theme.on_primary
                    btn.label.bg = btn.bg
            else:
                btn.bg = self.color_theme.surface_variant
                if hasattr(btn, "label") and btn.label:
                    btn.label.fg = self.color_theme.on_surface
                    btn.label.bg = btn.bg
            btn.invalidate()
        self._pages[index].invalidate()
        if self._change_callback:
            self._change_callback(self)

    @property
    def index(self):
        return self._value

    @index.setter
    def index(self, value):
        self.set_index(value)

    @property
    def pages(self):
        return list(self._pages)


# Alias used in the plan / docs.
TabBar = TabView
