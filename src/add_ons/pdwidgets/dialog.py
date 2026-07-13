# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from eventsys import events

from ._constants import ALIGN, ICON_SIZE, PAD
from ._util import _root_screen
from .button import Button
from .card import Card
from .label import Label
from .widget import Widget


class Dialog(Widget):
    def __init__(
        self,
        parent: Widget,
        message="",
        title=None,
        buttons=None,
        on_result=None,
        fg=None,
        bg=None,
        w=None,
        h=None,
        font=None,
        scrim=None,
    ):
        """
        Initialize a Dialog: a modal message box centered over the screen.

        The dialog is a full-screen overlay (painted with an opaque ``scrim`` —
        the pure-Python framebuffer has no alpha blending, so the backdrop is a
        solid muted color rather than a translucent dim) holding a centered
        :class:`Card` with a title, a message and one or more action buttons.
        While shown it grabs modal pointer capture so the underlying UI is inert.
        Clicking a button closes the dialog and invokes ``on_result`` with that
        button's label.

        Args:
            parent (Widget): The parent widget or screen; the overlay is attached
                to the root screen so it covers the whole display.
            message (str): The message body text.
            title (str): Optional title shown at the top of the card.
            buttons (list): Button labels (default ``["OK"]``).
            on_result (callable): Called as ``on_result(label)`` when a button is
                pressed (also fired before the dialog hides).
            fg (int): Text color; defaults to ``on_surface``.
            bg (int): Card color; defaults to ``surface``.
            w (int): Card width (auto-sized when omitted).
            h (int): Card height (auto-sized when omitted).
            font (module): Optional proportional font module for the title.
            scrim (int): Backdrop fill color; defaults to ``color_theme.shadow``.

        Usage:
            dlg = Dialog(screen, "Power off?", title="Confirm",
                         buttons=["Cancel", "OK"], on_result=handle)
            dlg.show()
        """
        screen = _root_screen(parent)
        display = parent.display
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        self.scrim = scrim if scrim is not None else parent.color_theme.shadow
        self.on_result = on_result
        super().__init__(
            screen, 0, 0, display.width, display.height, fg=fg, bg=None, visible=False
        )
        w = w or min(display.width - 2 * ICON_SIZE.LARGE, ICON_SIZE.LARGE * 8)
        h = h or min(display.height - 2 * ICON_SIZE.LARGE, ICON_SIZE.LARGE * 5)
        self.card = Card(
            self, w=w, h=h, align=ALIGN.CENTER, fg=fg, bg=bg, title=title, font=font, shadow=4
        )
        Label(
            self.card,
            value=message,
            align=ALIGN.CENTER,
            y=-ICON_SIZE.SMALL,
            fg=fg,
            bg=bg,
        )
        labels = list(buttons) if buttons else ["OK"]
        gap = PAD * 3
        n = len(labels)
        btn_w = (w - gap * (n + 1)) // n
        for i, lbl in enumerate(labels):
            btn = Button(
                self.card,
                w=btn_w,
                x=gap + i * (btn_w + gap),
                y=-gap,
                align=ALIGN.BOTTOM_LEFT,
                align_to=self.card,
                label=lbl,
                radius=6,
            )
            btn.add_event_cb(events.MOUSEBUTTONDOWN, self._make_result(lbl))

    def _make_result(self, label):
        """Return a callback that reports ``label`` and closes the dialog."""

        def result(data=None, event=None):
            if self.on_result:
                self.on_result(label)
            self.hide_dialog()

        return result

    def show(self):
        """Show the dialog and grab modal pointer capture."""
        self.visible = True
        self.set_modal(True)
        self.invalidate()

    def hide_dialog(self):
        """Hide the dialog and release modal pointer capture."""
        self.set_modal(False)
        self.visible = False

    def draw(self, area=None):
        """
        Paint the opaque scrim behind the card.

        A full draw fills the whole screen; a child's ``parent.draw(child.area)``
        request fills just that sub-region with the scrim so the card's children
        are not erased.
        """
        area = area or self.area
        self.display.framebuf.fill_rect(*area, self.scrim)
