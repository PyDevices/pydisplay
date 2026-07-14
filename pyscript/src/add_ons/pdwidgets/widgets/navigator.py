# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ..widget import Widget
from .page import Page


class Navigator(Widget):
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
    ):
        """
        Stack of :class:`Page` children with push / pop navigation.

        Only the top page is visible. Typical pattern::

            nav = Navigator(screen)
            home = Page(nav, title="Home")
            nav.push(home)
            detail = Page(nav, title="Detail", visible=False)
            # later:
            nav.push(detail)
            nav.pop()
        """
        w = w or parent.width
        h = h or parent.height
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
        self._stack = []

    @property
    def top(self):
        """The visible top page, or ``None`` if empty."""
        return self._stack[-1] if self._stack else None

    def push(self, page: Page):
        """Show ``page`` and hide the previous top page."""
        if page.parent is not self:
            page.parent = self
        if self._stack:
            self._stack[-1].visible = False
        page.visible = True
        if page not in self._stack:
            self._stack.append(page)
        page.invalidate()
        return page

    def pop(self):
        """Hide the top page and reveal the one under it. Returns the popped page."""
        if len(self._stack) <= 1:
            return None
        top = self._stack.pop()
        top.visible = False
        self._stack[-1].visible = True
        self._stack[-1].invalidate()
        return top

    def replace(self, page: Page):
        """Replace the entire stack with a single page."""
        for p in self._stack:
            p.visible = False
        self._stack.clear()
        return self.push(page)
