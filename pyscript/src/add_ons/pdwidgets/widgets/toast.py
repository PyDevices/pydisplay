# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ALIGN, ICON_SIZE, PAD, TEXT_SIZE
from .._util import _root_screen
from ..widget import Widget
from .label import Label

try:
    from time import ticks_ms
except ImportError:
    from multimer import ticks_ms


class Toast(Widget):
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
        visible=False,
        value="",
        padding=None,
        duration_ms=2000,
        radius=8,
    ):
        """
        Transient bottom banner for non-modal feedback.

        Call :meth:`show` with a message; the toast auto-hides after
        ``duration_ms`` using the display's task list.
        """
        screen = _root_screen(parent)
        display = parent.display
        w = w or min(display.width - 2 * PAD, ICON_SIZE.LARGE * 8)
        h = h or ICON_SIZE.MEDIUM + 2 * PAD
        theme = parent.color_theme
        bg = bg if bg is not None else theme.on_surface
        fg = fg if fg is not None else theme.surface
        self.duration_ms = duration_ms
        self.radius = radius
        self._task = None
        self._hide_at = 0
        super().__init__(
            screen,
            x,
            y,
            w,
            h,
            align if align is not None else ALIGN.BOTTOM,
            align_to,
            fg,
            bg,
            visible,
            value,
            padding,
        )
        self.set_position(y=-PAD * 3)
        self.message = Label(
            self,
            value=value or "",
            align=ALIGN.CENTER,
            fg=fg,
            bg=bg,
            text_height=TEXT_SIZE.MEDIUM,
        )

    def show(self, message=None, duration_ms=None):
        """Show the toast with ``message`` (keeps current text if omitted)."""
        if message is not None:
            self.message.set_value(message)
            self._value = message
        if duration_ms is not None:
            self.duration_ms = duration_ms
        self._hide_at = ticks_ms() + self.duration_ms
        self.visible = True
        self.invalidate()
        if self._task is None:
            self._task = self.display.add_task(self._poll, 100)

    def _poll(self):
        if not self.visible:
            return
        if ticks_ms() >= self._hide_at:
            self.visible = False
            if self._task is not None:
                try:
                    self.display.remove_task(self._task)
                except ValueError:
                    pass
                self._task = None

    def draw(self, area=None):
        """Draw a rounded toast pill."""
        if area is not None:
            self.display.framebuf.fill_rect(*area, self.bg)
            return
        self.parent.draw(self.area)
        self.display.framebuf.round_rect(*self.padded_area, self.radius, self.bg, f=True)
