"""Keypad must apply translate() so scrolled displays map touch correctly."""

import sys

sys.path[:0] = ["src/lib", "src/add_ons"]

from touch_keypad import Keypad  # noqa: E402

from eventsys import events  # noqa: E402


class MockBroker:
    def __init__(self):
        self._subs = {}

    def subscribe(self, cb, event_types=None):
        for et in event_types or []:
            self._subs.setdefault(et, set()).add(cb)

    def inject(self, event):
        for cb in self._subs.get(event.type, ()):
            cb(event)


def evt(etype, pos):
    class E:
        pass

    e = E()
    e.type = etype
    e.button = 1
    e.pos = pos
    return e


def translate_scrolled(point):
    x, y = point
    # Window y=200 -> logical y=280 (as if vscroll shows keypad region)
    return x, y + 80


broker = MockBroker()
keypad = Keypad(broker, 2, 233, 7 * 45, 3 * 45, cols=7, rows=3, translate=translate_scrolled)
# Window click on visible key row; logical y must be ~250 after translate
window_pos = (50, 200)

broker.inject(evt(events.MOUSEBUTTONDOWN, window_pos))
broker.inject(evt(events.MOUSEBUTTONUP, window_pos))
clicks = keypad.read()

print(f"window_pos={window_pos!r} logical_y={translate_scrolled(window_pos)[1]}")
print(f"read={clicks!r}")
print(f"hit={'yes' if clicks else 'no'}")
