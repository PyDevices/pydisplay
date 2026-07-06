# Input drivers

Helpers for wiring physical buttons and encoders into `eventsys`.

## `keypad_gpio.py`

Maps GPIO buttons to `eventsys.KEYPAD` key codes.

```python
from keypad_gpio import GPIOButtons, MAGTAG_BUTTON_KEYS
from eventsys.keys import Keys

buttons = GPIOButtons({
    "a": (board.BUTTON_A, Keys.K_a),
    "b": (board.BUTTON_B, Keys.K_b),
})

broker.create(type=eventsys.KEYPAD, read=buttons.read)
```

Used by MagTag, PyBadge, and similar boards with front-panel buttons.
