# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`touch_keypad`
====================================================

Matrix keypad helper for touch displays on displaysys.

Divides the display into a grid of rows and columns.
Returns the key number of the associated cell pressed.

Also passes through the key from any KEYDOWN events from the display.

Usage:
from touch_keypad import Keypad
from board_config import display_drv, broker

keys = [1, 2, 3, "A", "B", "C", "play", "pause", "esc"]
keypad = Keypad(broker.poll, 0, 0, display_drv.width, display_drv.height, cols=3, rows=3, keys=keys)
while True:
    if key := keypad.read():
        print(key)
"""

from eventsys import events

try:
    from graphics import Area
except ImportError:
    print(
        "touch_keypad:  graphics module not found.  Keypad.areas attribute will not be available."
    )
    Area = None


class Keypad:
    def __init__(self, broker, x, y, w, h, cols=3, rows=3, keys=None, translate=None):
        self._keys = keys if keys else list(range(cols * rows))
        self._broker = broker
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cols = cols
        self.rows = rows
        self.key_width = kw = w / cols
        self.key_height = kh = h / rows
        self._translate = translate or (lambda point: point)
        if Area:
            self.areas = [
                Area(int(x + kw * i), int(y + kh * j), int(kw), int(kh))
                for j in range(rows)
                for i in range(cols)
            ]
        self._state = {k:False for k in self._keys}
        self._broker.subscribe(self.callback, event_types=[events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP, events.KEYDOWN, events.KEYUP])
        

    def callback(self, event):
        print(f"Touchpad callback: {event}")
        if event.type in [events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP] and event.button == 1:
            x, y = event.pos
            if x < self.x or x > self.x + self.w or y < self.y or y > self.y + self.h:
                return
            col = int((x - self.x) / self.key_width)
            row = int((y - self.y) / self.key_height)
            # BUG:  Sometimes throws an IndexError in Wokwi if the touch is on the last line
            # Instead of doing a bounds check we just catch the exception.
            try:
                key = self._keys[row * self.cols + col]
                self._state[key] = event.type == events.MOUSEBUTTONDOWN
                return
            except IndexError:
                return

        if event.type in [events.KEYDOWN, events.KEYUP]:
            key = event.key
            if key in self._keys:
                self._state[key] = event.type == events.KEYDOWN

    def read(self):
        return [k for k, v in self._state.items() if v]
