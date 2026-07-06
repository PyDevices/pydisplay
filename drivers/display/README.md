display_drivers
===============
3 formats are supported 
- init sequence as a bytearray in CircuitPython DisplayIO format, for example [gc9a01](gc9a01.py)
- init sequence as a list of tuples, for example [st7789](st7789.py)
- init sequence handled manually, for example [st7796](st7796.py)

OLED, E-paper, and community displayio drivers are vendored from Adafruit and Community bundles.
Run `python3 scripts/vendor_circuitpython_drivers.py --all` to refresh from upstream.

See [driver inventory](../../docs/hardware/driver-inventory.md) and [display interfaces](../../docs/hardware/display-interfaces.md).