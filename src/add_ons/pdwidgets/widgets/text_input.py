# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from ._constants import PAD, TEXT_SIZE, TEXT_WIDTH
from .widget import Widget


class TextInput(Widget):
    _focused = None  # the TextInput currently receiving key events, if any

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
        hint="",
        text_height=TEXT_SIZE.LARGE,
        radius=6,
        max_length=None,
    ):
        """
        Initialize a TextInput: a single-line editable text field.

        Tap the field to focus it (a text cursor appears and the border
        highlights); typing appends printable characters, Backspace deletes, and
        Enter releases focus. Only the focused field consumes key events, so
        several inputs can coexist on one screen.

        Args:
            parent (Widget): The parent widget or screen that contains this input.
            x (int): The x-coordinate of the input.
            y (int): The y-coordinate of the input.
            w (int): The width of the input (defaults to the parent width).
            h (int): The height of the input.
            align (int): The alignment of the input.
            align_to (Widget): The widget to align to.
            fg (int): The text color; defaults to ``on_surface``.
            bg (int): The field color; defaults to ``surface``.
            visible (bool): The visibility of the input.
            value (str): The initial text content.
            padding (tuple): The padding on each side of the input.
            hint (str): Placeholder text shown (dimmed) while empty.
            text_height (int): The romfont text height (default TEXT_SIZE.LARGE).
            radius (int): The corner radius of the field (default 6).
            max_length (int): Maximum number of characters, or ``None``.

        Usage:
            name = TextInput(card, hint="Your name", max_length=16)
            name.set_change_cb(lambda s: print(s.value))
        """
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        value = value if value is not None else ""
        w = w or parent.width
        h = h or text_height + 3 * PAD
        self.hint = hint
        self.text_height = text_height
        self.radius = radius
        self.max_length = max_length
        self.focused = False
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._focus)
        self.add_event_cb(events.KEYDOWN, self._key)

    def _focus(self, data=None, event=None):
        """Take keyboard focus (releasing any previously focused input)."""
        prev = TextInput._focused
        if prev is not None and prev is not self:
            prev.focused = False
            prev.invalidate()
        TextInput._focused = self
        if not self.focused:
            self.focused = True
            self.invalidate()

    def _key(self, data=None, event=None):
        """Edit the text on key press, but only when this input is focused."""
        if not self.focused or TextInput._focused is not self:
            return
        key = event.key
        if key == 8:  # Backspace
            if self._value:
                self.value = self._value[:-1]
        elif key == 13:  # Enter / Return releases focus
            self.focused = False
            TextInput._focused = None
            self.invalidate()
        elif 32 <= key < 127 and (self.max_length is None or len(self._value) < self.max_length):
            self.value = self._value + chr(key)

    def draw(self, _=None):
        """Draw the field box, its text or hint, and the cursor when focused."""
        self.parent.draw(self.area)
        pa = self.padded_area
        border = self.color_theme.primary if self.focused else self.color_theme.outline
        self.display.framebuf.round_rect(*pa, self.radius, self.bg, f=True)
        self.display.framebuf.round_rect(*pa, self.radius, border, f=False)
        tx = pa.x + PAD + self.radius
        ty = pa.y + (pa.h - self.text_height) // 2
        text = self._value or ""
        if text:
            self.display.framebuf.text(text, tx, ty, self.fg, height=self.text_height)
        elif self.hint:
            self.display.framebuf.text(
                self.hint, tx, ty, self.color_theme.tertiary, height=self.text_height
            )
        if self.focused:
            cx = tx + len(text) * TEXT_WIDTH
            self.display.framebuf.fill_rect(cx, ty, 1, self.text_height, self.fg)
