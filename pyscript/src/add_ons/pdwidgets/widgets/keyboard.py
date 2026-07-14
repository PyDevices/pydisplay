# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from .._constants import ALIGN, PAD, TEXT_SIZE
from .._util import _root_screen
from ..widget import Widget
from .button import Button
from .text_input import TextInput

_ROWS = (
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
)


class Keyboard(Widget):
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
        value=None,
        padding=None,
        target=None,
        row_height=None,
    ):
        """
        On-screen QWERTY keyboard that feeds the focused field.

        Attach to a screen, call :meth:`show` when an input is focused (or pass
        ``target``). Keys synthesize ``events.Key`` and forward them to the
        target's ``_key`` handler. The default target is
        ``display.focus_manager.focused`` (with ``TextInput._focused`` as
        fallback).
        """
        screen = _root_screen(parent)
        display = parent.display
        w = w or display.width
        rh = row_height or (TEXT_SIZE.LARGE + 2 * PAD)
        # 3 letter rows + space/backspace/enter row
        h = h or rh * 4 + PAD
        bg = bg if bg is not None else parent.color_theme.surface_variant
        fg = fg if fg is not None else parent.color_theme.on_surface
        self.target = target
        self.row_height = rh
        self._shifted = False
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
            padding or (PAD, PAD, PAD, PAD),
        )
        self._build_keys()

    def _build_keys(self):
        gap = 2
        for r, chars in enumerate(_ROWS):
            n = len(chars)
            key_w = (self.width - 2 * PAD - gap * (n - 1)) // n
            y = r * self.row_height
            for i, ch in enumerate(chars):
                btn = Button(
                    self,
                    x=PAD + i * (key_w + gap),
                    y=y,
                    w=key_w,
                    h=self.row_height - gap,
                    label=ch,
                    radius=3,
                    text_height=TEXT_SIZE.MEDIUM,
                    bg=self.color_theme.surface,
                    text_color=self.fg,
                )
                btn.value = ch
                btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_char_cb(ch))
        # Bottom row: shift, space, backspace, enter
        y = 3 * self.row_height
        specials = [
            ("⇧", "shift", self.width // 8),
            ("space", " ", self.width // 2),
            ("⌫", "bksp", self.width // 8),
            ("↵", "enter", self.width // 8),
        ]
        x = PAD
        for label, code, kw in specials:
            btn = Button(
                self,
                x=x,
                y=y,
                w=kw - gap,
                h=self.row_height - gap,
                label=label if label != "space" else " ",
                radius=3,
                text_height=TEXT_SIZE.MEDIUM,
                bg=self.color_theme.primary_variant
                if code in ("shift", "enter", "bksp")
                else self.color_theme.surface,
                text_color=self.color_theme.on_primary
                if code in ("shift", "enter", "bksp")
                else self.fg,
            )
            if code == "shift":
                btn.add_event_cb(events.MOUSEBUTTONDOWN, self._toggle_shift)
            elif code == " ":
                btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_char_cb(" "))
            elif code == "bksp":
                btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_key_cb(8))
            elif code == "enter":
                btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_key_cb(13))
            x += kw

    def _toggle_shift(self, data=None, event=None):
        self._shifted = not self._shifted

    def _make_char_cb(self, ch):
        def cb(data=None, event=None):
            out = ch.upper() if self._shifted else ch
            self._emit_key(ord(out) if len(out) == 1 else 32, out)

        return cb

    def _make_key_cb(self, keycode):
        def cb(data=None, event=None):
            self._emit_key(keycode, "")

        return cb

    def _emit_key(self, keycode, name):
        target = self.target
        if target is None:
            target = self.display.focus_manager.focused
        if target is None:
            target = TextInput._focused
        if target is None:
            return
        ev = events.Key(
            events.KEYDOWN, name or chr(keycode) if 32 <= keycode < 127 else "", keycode, 0, 0, 0
        )
        target._key(target, ev)

    def show(self, target=None):
        """Show the keyboard, optionally binding ``target`` TextInput."""
        if target is not None:
            self.target = target
        self.visible = True
        self.invalidate()

    def hide_keyboard(self):
        """Hide the keyboard."""
        self.visible = False
