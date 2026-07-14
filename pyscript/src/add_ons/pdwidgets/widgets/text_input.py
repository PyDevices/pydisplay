# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events
from eventsys.keys import Keys

from .._constants import PAD, TEXT_SIZE, TEXT_WIDTH
from ..widget import Widget


class TextInput(Widget):
    _focused = None  # back-compat alias; prefer display.focus_manager.focused

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
        Enter releases focus. Focus order is managed by
        :class:`~pdwidgets._focus.FocusManager` (Tab / Shift-Tab / arrows).
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
        self.display.focus_manager.register(self)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._focus)
        self.add_event_cb(events.KEYDOWN, self._key)

    def _focus(self, data=None, event=None):
        """Take keyboard focus via the display FocusManager."""
        self.display.focus_manager.focus(self)
        TextInput._focused = self

    def _key(self, data=None, event=None):
        """Edit the text on key press, but only when this input is focused."""
        fm = self.display.focus_manager
        if not self.focused or fm.focused is not self:
            return
        key = event.key
        if key == Keys.K_BACKSPACE:
            if self._value:
                self.value = self._value[:-1]
        elif key == Keys.K_RETURN:
            self.display.focus_manager.blur()
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
        text = self._display_text()
        if text:
            self.display.framebuf.text(text, tx, ty, self.fg, height=self.text_height)
        elif self.hint:
            self.display.framebuf.text(
                self.hint, tx, ty, self.color_theme.tertiary, height=self.text_height
            )
        if self.focused:
            cx = tx + len(text) * TEXT_WIDTH
            self.display.framebuf.fill_rect(cx, ty, 1, self.text_height, self.fg)

    def _display_text(self):
        """Text shown in the field (PasswordField overrides to mask)."""
        return self._value or ""
