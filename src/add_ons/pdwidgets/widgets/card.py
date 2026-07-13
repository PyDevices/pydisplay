# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ._constants import ALIGN, PAD
from .label import Label
from .widget import Widget


class Card(Widget):
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
        radius=8,
        shadow=2,
        title=None,
        font=None,
    ):
        """
        Initialize a Card: a rounded, optionally-shadowed container for grouping
        other widgets.

        The card paints a rounded ``surface`` rectangle (with a cheap fake drop
        shadow) and, optionally, a title along its top. Add child widgets to it
        exactly like any other container.

        Args:
            parent (Widget): The parent widget or screen that contains this card.
            x (int): The x-coordinate of the card.
            y (int): The y-coordinate of the card.
            w (int): The width of the card.
            h (int): The height of the card.
            align (int): The alignment of the card.
            align_to (Widget): The widget to align to.
            fg (int): The foreground (text) color; defaults to ``on_surface``.
            bg (int): The card surface color; defaults to ``surface``.
            visible (bool): The visibility of the card.
            value (Any): User-assigned value of the card.
            padding (tuple): The padding on each side of the card.
            radius (int): The corner radius of the card (default is 8).
            shadow (int): Fake drop-shadow offset in pixels (0 disables).
            title (str): Optional title drawn along the top of the card.
            font (module): Optional proportional font module for the title.

        Usage:
            card = Card(screen, w=200, h=120, title="Settings")
            Switch(card, align=pd.ALIGN.CENTER)
        """
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        self.radius = radius
        self.shadow = shadow
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        self.title_label = None
        if title:
            self.title_label = Label(
                self,
                value=title,
                x=radius,
                y=PAD,
                align=ALIGN.TOP_LEFT,
                fg=fg,
                bg=bg,
                font=font,
            )

    def draw(self, area=None):
        """
        Draw the card's shadow and rounded surface.

        When a child asks the card to repaint just its sub-area (via
        ``parent.draw(child.area)``), only that region is refilled with the card
        color so sibling widgets are not erased; a full (``area is None``) draw
        repaints the shadow and rounded surface.
        """
        if area is not None:
            self.display.framebuf.fill_rect(*area, self.bg)
            return
        self.parent.draw(self.area)
        pa = self.padded_area
        if self.shadow:
            self.display.framebuf.round_rect(
                pa.x + self.shadow,
                pa.y + self.shadow,
                pa.w,
                pa.h,
                self.radius,
                self.color_theme.shadow,
                f=True,
            )
        self.display.framebuf.round_rect(*pa, self.radius, self.bg, f=True)
