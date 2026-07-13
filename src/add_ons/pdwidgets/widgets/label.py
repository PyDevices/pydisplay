# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from .._constants import ALIGN, TEXT_SIZE, TEXT_WIDTH
from ..widget import Widget


class Label(Widget):
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
        text_height=TEXT_SIZE.LARGE,
        scale=1,
        inverted=False,
        font_data=None,
        font=None,
    ):
        """
        Initialize a Label widget to display text.

        By default the built-in 8-pixel-wide romfont is used. Passing ``font``
        (a proportional bitmap font module from the ``write_font_converter``
        pipeline, e.g. ``chango_32``) renders the text with the optional
        ``add_ons/tft_write`` renderer instead — see the module docstring note
        on that dependency. Proportional text is opaque, so a solid ``bg`` is
        used (the parent's ``bg`` when none is given).

        Args:
            parent (Widget): The parent widget or screen that contains this label.
            x (int): The x-coordinate of the label.
            y (int): The y-coordinate of the label.
            w (int): The width of the label.
            h (int): The height of the label.
            align (int): The alignment of the label.
            align_to (Widget): The widget to align to.
            fg (int): The color of the text.
            bg (int): The background color of the label.
            visible (bool): The visibility of the label.
            value (str): The text content of the label.
            padding (tuple): The padding on each side of the label.
            text_height (int): The height of the romfont text (default TEXT_SIZE.LARGE).
            scale (int): The scale of the romfont text (default is 1).
            inverted (bool): Invert the romfont text (default is False).
            font_data (str): Alternate romfont file/memoryview for the text.
            font (module): Proportional bitmap font module (``tft_write`` style);
                when given, overrides romfont rendering and sizing.
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        padding = padding if padding is not None else (0, 0, 0, 0)
        value = value if value is not None else ""
        self._font = font
        if font is not None:
            from tft_write import write_width

            w = w or write_width(font, value) + padding[0] + padding[2]
            h = h or font.HEIGHT + padding[1] + padding[3]
            bg = bg if bg is not None else parent.bg
        else:
            w = w or len(value) * TEXT_WIDTH * scale + padding[0] + padding[2]
            h = h or text_height * scale + padding[1] + padding[3]
        align = align if align is not None else ALIGN.CENTER
        self.text_height = text_height
        self.scale = scale
        self._inverted = inverted
        self._font_data = font_data
        bg = bg if bg is not None else parent.color_theme.transparent
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def draw(self, _=None):
        """
        Draw the label's text on the screen, using absolute coordinates.
        Optionally fills the background first if `bg` is set.
        """
        x, y, _, _ = self.padded_area
        if self._font is not None:
            # Proportional font: tft_write fills each glyph's background itself.
            from tft_write import write as _tft_write

            bg = self.bg if self.bg is not self.parent.color_theme.transparent else self.parent.bg
            self.display.framebuf.fill_rect(*self.padded_area, bg)
            _tft_write(self.display.framebuf, self._font, self.value, x, y, self.fg, bg)
            return
        if self.bg is not self.parent.color_theme.transparent:
            self.display.framebuf.fill_rect(
                *self.padded_area, self.bg
            )  # Draw background if bg is specified
        self.display.framebuf.text(
            self.value,
            x,
            y,
            self.fg,
            height=self.text_height,
            scale=self.scale,
            inverted=self._inverted,
            font_data=self._font_data,
        )

    @property
    def char_width(self):
        return TEXT_WIDTH * self.scale

    @property
    def char_height(self):
        return self.text_height * self.scale
