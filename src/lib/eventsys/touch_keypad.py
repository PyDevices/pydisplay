# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Optional eventsys mapper: on-screen cell-grid keypad over pointer events.

``TouchKeypad`` is **not** a :class:`~eventsys.KeypadDevice`.  It does not poll
hardware or enqueue events.  It subscribes to a :class:`~eventsys.Runtime` and
maps primary-button pointer presses inside a rectangle into a grid of app key
ids.  Matching ``KEYDOWN`` / ``KEYUP`` values that appear in ``keys`` are
tracked the same way.

Import explicitly (not loaded by ``import eventsys``)::

    from eventsys.touch_keypad import TouchKeypad

Callback idiom (canonical — runtime auto-service dispatches)::

    from board_config import display_drv, runtime
    from eventsys.touch_keypad import TouchKeypad

    keys = [1, 2, 3, "A", "B", "C", "play", "pause", "esc"]
    pad = TouchKeypad(
        runtime, 0, 0, display_drv.width, display_drv.height,
        cols=3, rows=3, keys=keys,
        on_press=lambda key: print("down", key),
        on_release=lambda key: print("up", key),
    )
    runtime.run_forever()

Poll idiom (legacy)::

    pad = TouchKeypad(runtime, 0, 0, display_drv.width, display_drv.height,
                      cols=3, rows=3, keys=keys)
    while True:
        runtime.poll()
        if pressed := pad.read():
            print(pressed)
        # Continuous movement: pad.read_held()
"""

from ._events import events

try:
    from graphics import Area
except ImportError:
    print("eventsys.touch_keypad: graphics not found; TouchKeypad.areas unavailable.")
    Area = None


class TouchKeypad:
    """Map a screen rectangle into a grid of app keys (pointer + optional keys).

    Subscribes to ``MOUSEBUTTONDOWN`` / ``MOUSEBUTTONUP`` (button 1) and
    ``KEYDOWN`` / ``KEYUP`` on ``runtime``.  Grid cells use ``keys`` (default
    ``0 .. cols*rows-1``).  Optional ``on_press`` / ``on_release`` fire from
    dispatch; ``read()`` / ``read_held()`` support poll loops.
    """

    def __init__(
        self,
        runtime,
        x,
        y,
        w,
        h,
        cols=3,
        rows=3,
        keys=None,
        translate=None,
        on_press=None,
        on_release=None,
    ):
        self._keys = keys if keys else list(range(cols * rows))
        self._runtime = runtime
        # Optional push callbacks: fired from event dispatch so the app need
        # not poll.  ``read()`` still works for legacy poll loops.
        self._on_press = on_press
        self._on_release = on_release
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
        self._state = dict.fromkeys(self._keys, False)
        self._clicks = []
        self._runtime.on(
            [events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP, events.KEYDOWN, events.KEYUP],
            self.callback,
        )

    def callback(self, event):
        if event.type in [events.MOUSEBUTTONDOWN, events.MOUSEBUTTONUP] and event.button == 1:
            x, y = self._translate(event.pos)
            if x < self.x or x > self.x + self.w or y < self.y or y > self.y + self.h:
                return
            col = int((x - self.x) / self.key_width)
            row = int((y - self.y) / self.key_height)
            # BUG: Sometimes IndexError on Wokwi if touch is on the last line;
            # catch instead of a bounds check.
            try:
                key = self._keys[row * self.cols + col]
                pressed = event.type == events.MOUSEBUTTONDOWN
                if pressed:
                    self._clicks.append(key)
                self._state[key] = pressed
                self._dispatch(key, pressed)
                return
            except IndexError:
                return

        if event.type in [events.KEYDOWN, events.KEYUP]:
            key = event.key
            if key in self._keys:
                pressed = event.type == events.KEYDOWN
                if pressed:
                    self._clicks.append(key)
                self._state[key] = pressed
                self._dispatch(key, pressed)

    def _dispatch(self, key, pressed):
        cb = self._on_press if pressed else self._on_release
        if cb is not None:
            cb(key)

    def read(self):
        """Return keys pressed since the last ``read()`` (edge triggered)."""
        if not self._clicks:
            return None
        clicks = self._clicks
        self._clicks = []
        return clicks

    def read_held(self):
        """Return keys currently held down (level triggered)."""
        return [k for k, v in self._state.items() if v]
