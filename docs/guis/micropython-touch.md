# MicroPython-Touch

[MicroPython-Touch](https://github.com/peterhinch/micropython-touch) by Peter Hinch provides widgets and async UI patterns for MicroPython.

## Requirements

- pydisplay `displaysys` + `eventsys`
- `add_ons/displaybuf.py` (DisplayBuffer)
- `hardware_setup.py` from MicroPython-Touch
- MicroPython only (not CircuitPython or CPython)

## Config

Copy `hardware_setup.py` from the MicroPython-Touch repo and point it at your pydisplay `board_config.py`.

## Examples

MicroPython-Touch demos import as:

```python
import lib.path
import gui.demos.various  # external MicroPython-Touch tree
```

pydisplay examples such as `nano_gui_simpletest.py` show related patterns.

## Fonts

Peter Hinch's **Writer** class works on MicroPython but does not return `Area` objects for partial refresh.
