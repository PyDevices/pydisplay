# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from .._constants import ALIGN, ICON_SIZE, PAD
from .._themes import icon_theme
from .._util import _root_screen
from ..widget import Widget
from .button import Button
from .card import Card
from .icon import Icon
from .label import Label


class Dropdown(Widget):
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
        options=None,
        radius=6,
    ):
        """
        Initialize a Dropdown: a header button that reveals a popup option list.

        Tapping the header opens a small popup (a shadowed :class:`Card` of
        option buttons) over the screen; tapping an option selects it, updates
        ``value`` and closes the popup; tapping anywhere else also closes it. The
        popup uses modal pointer capture (see :meth:`Widget.set_modal`) so the
        rest of the UI is inert while it is open.

        Args:
            parent (Widget): The parent widget or screen that contains this dropdown.
            x (int): The x-coordinate of the dropdown.
            y (int): The y-coordinate of the dropdown.
            w (int): The width of the dropdown header.
            h (int): The height of the dropdown header.
            align (int): The alignment of the dropdown.
            align_to (Widget): The widget to align to.
            fg (int): The text/arrow color; defaults to ``on_surface``.
            bg (int): The header color; defaults to ``surface``.
            visible (bool): The visibility of the dropdown.
            value (str): The initially selected option (defaults to the first).
            padding (tuple): The padding on each side of the dropdown.
            options (list): The list of option strings.
            radius (int): The corner radius of the header/popup (default 6).

        Usage:
            dd = Dropdown(card, options=["Low", "Medium", "High"])
            dd.set_change_cb(lambda s: print("chose", s.value))
        """
        self.options = list(options) if options else []
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        w = w or ICON_SIZE.LARGE * 4
        h = h or ICON_SIZE.LARGE
        self.radius = radius
        if value is None and self.options:
            value = self.options[0]
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self._open = False
        self._open_event = None
        self._arrow = Icon(
            self,
            align=ALIGN.RIGHT,
            fg=fg,
            bg=bg,
            value=icon_theme.dropdown(ICON_SIZE.SMALL),
        )
        self._sel_label = Label(
            self, value=str(value or ""), x=PAD + radius, align=ALIGN.LEFT, fg=fg, bg=bg
        )
        # A full-screen, transparent overlay on the root screen grabs modal
        # pointer capture while open; the option Card lives inside it.
        screen = _root_screen(self)
        self._overlay = Widget(
            screen, 0, 0, self.display.width, self.display.height, visible=False
        )
        # A None bg makes the overlay's draw a no-op (Widget.__init__ would
        # otherwise inherit the parent's bg and repaint the whole screen); the
        # overlay is a transparent, click-catching modal layer only.
        self._overlay.bg = None
        self._overlay.add_event_cb(events.MOUSEBUTTONDOWN, self._on_overlay)
        option_h = ICON_SIZE.LARGE
        self._panel = Card(
            self._overlay,
            w=self.width,
            h=option_h * max(len(self.options), 1),
            align=ALIGN.OUTER_BOTTOM,
            align_to=self,
            radius=radius,
            shadow=3,
        )
        self._option_buttons = []
        for i, opt in enumerate(self.options):
            btn = Button(
                self._panel,
                w=self.width,
                h=option_h,
                y=i * option_h,
                align=ALIGN.TOP_LEFT,
                align_to=self._panel,
                label=str(opt),
                radius=0,
                bg=self._panel.bg,
                text_color=fg,
            )
            btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_select(opt))
            self._option_buttons.append(btn)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._toggle_open)

    def _make_select(self, option):
        """Return a callback that selects ``option`` and closes the popup."""

        def select(data=None, event=None):
            self.value = option
            self._close()

        return select

    def _toggle_open(self, data=None, event=None):
        """Open the popup when closed (tapping the header)."""
        if not self._open:
            self._open = True
            # Remember the opening event so the overlay's close-on-outside
            # handler ignores this same click (modal capture only kicks in on
            # the next event; without this the opening click would immediately
            # reach the now-visible overlay and close the popup).
            self._open_event = event
            self._overlay.visible = True
            self._overlay.set_modal(True)

    def _close(self):
        """Hide the popup and release modal capture."""
        if self._open:
            self._open = False
            self._overlay.set_modal(False)
            self._overlay.visible = False

    def _on_overlay(self, data=None, event=None):
        """Close the popup when the tap lands outside the option panel."""
        if event is self._open_event:
            return
        point = self.display.translate_point(event.pos)
        if not self._panel.area.contains(point):
            self._close()

    def changed(self):
        """Update the header label to the selected option."""
        self._sel_label.value = str(self._value or "")
        super().changed()

    def draw(self, area=None):
        """Draw the dropdown header (rounded surface); repaint sub-areas flat."""
        if area is not None:
            self.display.framebuf.fill_rect(*area, self.bg)
            return
        self.parent.draw(self.area)
        self.display.framebuf.round_rect(*self.padded_area, self.radius, self.bg, f=True)
        self.display.framebuf.round_rect(
            *self.padded_area, self.radius, self.color_theme.outline, f=False
        )
