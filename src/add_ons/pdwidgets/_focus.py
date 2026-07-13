# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Keyboard focus ring for pdwidgets (Tab / Shift-Tab / arrows)."""

from eventsys import events
from eventsys.keys import Keys


class FocusManager:
    """Tracks focusable widgets and moves focus without a pointer.

    Pointer modality (:meth:`Widget.set_modal`) remains separate: it captures
    mouse/touch only. FocusManager owns which field receives keystrokes.
    """

    def __init__(self):
        self._widgets = []
        self._index = -1

    @property
    def focused(self):
        if 0 <= self._index < len(self._widgets):
            return self._widgets[self._index]
        return None

    def register(self, widget):
        """Add ``widget`` to the focus ring (idempotent)."""
        if widget not in self._widgets:
            self._widgets.append(widget)

    def unregister(self, widget):
        """Remove ``widget`` from the focus ring."""
        if widget in self._widgets:
            i = self._widgets.index(widget)
            self._widgets.remove(widget)
            if self._index == i:
                self._index = -1
                if hasattr(widget, "focused"):
                    widget.focused = False
            elif self._index > i:
                self._index -= 1

    def focus(self, widget):
        """Give keyboard focus to ``widget`` (must be registered)."""
        if widget is None:
            self.blur()
            return
        if widget not in self._widgets:
            self.register(widget)
        prev = self.focused
        if prev is widget:
            return
        if prev is not None:
            if hasattr(prev, "focused"):
                prev.focused = False
            if hasattr(prev, "invalidate"):
                prev.invalidate()
        self._index = self._widgets.index(widget)
        if hasattr(widget, "focused"):
            widget.focused = True
        if hasattr(widget, "invalidate"):
            widget.invalidate()
        # Keep TextInput._focused in sync for soft-keyboard fallbacks.
        try:
            from .widgets.text_input import TextInput

            TextInput._focused = widget if isinstance(widget, TextInput) else None
        except ImportError:
            pass

    def blur(self):
        """Clear keyboard focus."""
        prev = self.focused
        self._index = -1
        if prev is not None:
            if hasattr(prev, "focused"):
                prev.focused = False
            if hasattr(prev, "invalidate"):
                prev.invalidate()
        try:
            from .widgets.text_input import TextInput

            TextInput._focused = None
        except ImportError:
            pass

    def focus_next(self, reverse=False):
        """Move focus to the next (or previous) visible focusable widget."""
        if not self._widgets:
            return
        n = len(self._widgets)
        step = -1 if reverse else 1
        start = self._index if self._index >= 0 else (0 if not reverse else n - 1)
        for i in range(1, n + 1):
            idx = (start + step * i) % n
            w = self._widgets[idx]
            if getattr(w, "visible", True):
                self.focus(w)
                return

    def handle_key(self, event):
        """Handle Tab / arrows for focus movement.

        Returns:
            bool: ``True`` if the event was consumed as a focus-change key.
        """
        if not self._widgets or event.type != events.KEYDOWN:
            return False
        key = event.key
        mod = getattr(event, "mod", 0) or 0
        shift = bool(mod & Keys.KMOD_SHIFT)
        if key == Keys.K_TAB:
            self.focus_next(reverse=shift)
            return True
        if key in (Keys.K_DOWN, Keys.K_RIGHT):
            self.focus_next(reverse=False)
            return True
        if key in (Keys.K_UP, Keys.K_LEFT):
            self.focus_next(reverse=True)
            return True
        return False
