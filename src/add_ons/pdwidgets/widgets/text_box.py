# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ._constants import DEFAULT_PADDING, PAD, TEXT_SIZE, TEXT_WIDTH
from .widget import Widget


class TextBox(Widget):
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
        format="",
        text_height=TEXT_SIZE.LARGE,
        scale=1,
        inverted=False,
        font_data=None,
    ):
        """
        Initialize a TextBox widget to display formatted text.

        Args:
            parent (Widget): The parent widget or screen that contains this text box.
            x (int): The x-coordinate of the text box.
            y (int): The y-coordinate of the text box.
            w (int): The width of the text box.
            h (int): The height of the text box.
            align (int): The alignment of the text box.
            align_to (Widget): The widget to align to.
            fg (int): The color of the text.
            bg (int): The background color of the text box.
            visible (bool): The visibility of the text box.
            value (str): The text content of the text box.
            padding (tuple): The padding on each side of the text box.
            format (str): The format string for the text.
            text_height (int): The height of the text (default is TEXT_SIZE.LARGE).
            scale (int): The scale of the text (default is 1).
            inverted (bool): The inversion of the text (default is False).
            font_data (str): The font file to use for the text.

        Usage:
            text_box = TextBox(screen, value="Hello, world!", format="{:>20}", text_height=TEXT_SIZE.LARGE)
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        padding = padding if padding is not None else DEFAULT_PADDING
        w = w or parent.width if parent else 60
        h = h or text_height * scale + padding[1] + padding[3]
        value = value if value is not None else ""
        self.format = format
        self.text_height = text_height
        self.scale = scale
        self._inverted = inverted
        self._font_data = font_data
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def draw(self, _=None):
        """
        Draw the label's text on the screen, using absolute coordinates.
        """
        pa = self.padded_area
        self.display.framebuf.fill_rect(*pa, self.bg)
        y = pa.y + (pa.h - self.text_height * self.scale) // 2
        self.display.framebuf.text(
            f"{self.value:{self.format}}",
            pa.x + PAD,
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
