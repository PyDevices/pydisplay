# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ..widget import Widget


class Page(Widget):
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
        title=None,
    ):
        """
        Full-bleed content page for use with :class:`Navigator` / :class:`TabView`.

        Args:
            parent (Widget): Usually a :class:`Navigator` or screen.
            title (str): Optional string retained for app logic (not drawn).
            visible (bool): Start hidden when stacking under a Navigator.
        """
        w = w or parent.width
        h = h or parent.height
        bg = bg if bg is not None else parent.bg
        fg = fg if fg is not None else parent.fg
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
        self.title = title
