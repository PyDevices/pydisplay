"""GPIO button helper for eventsys KEYPAD on CircuitPython and MicroPython."""

try:
    from eventsys.keys import Keys
except ImportError:
    from keys import Keys


class GPIOButtons:
    """
    Map GPIO buttons (active-low by default) to keyboard key codes.

    Args:
        mapping: Dict of name -> (pin, key_code). *pin* is a DigitalInOut or Pin.
        active_low (bool): True when pressed reads low.
    """

    def __init__(self, mapping, *, active_low=True):
        self._buttons = [(pin, key) for pin, key in mapping.values()]
        self._active_low = active_low

    def read(self):
        """Return list of key codes for buttons currently pressed."""
        pressed = []
        for pin, key in self._buttons:
            value = pin.value
            if self._active_low:
                down = not value
            else:
                down = bool(value)
            if down:
                pressed.append(key)
        return pressed


# MagTag / PyBadge style letter keys
MAGTAG_BUTTON_KEYS = (Keys.K_a, Keys.K_b, Keys.K_c, Keys.K_d)
