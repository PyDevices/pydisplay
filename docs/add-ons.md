# Add-ons

Optional extensions in [`src/add_ons/`](https://github.com/PyDevices/pydisplay/tree/main/src/add_ons/). Not required for basic display and event use. API docs: [Add-ons Reference](reference/add_ons/).

## Install

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/add_ons.json", target="./add_ons")
```

## Path setup

```python
import add_ons.add_path
```

Or copy modules into `lib/` on your device.

## Notable modules

| Module | Purpose |
|--------|---------|
| `framebuf.py` | framebuf API on CPython/CircuitPython |
| `displaybuf.py` | Peter Hinch DisplayBuffer API |
| `bmp565.py` | RGB565 BMP read/write/stream |
| `console.py` | Terminal-style console widget |
| `pdwidgets/` | Cross-platform widget toolkit — [PyWidgets](guis/pywidgets.md) |
| `tft_text.py`, `tft_write.py` | russhughes font rendering |
| `png.py` | PNG support (experimental) |
| `touch_keypad.py` | On-screen keypad |

Many examples in `src/examples/` depend on add_ons. They are excluded from the micropython-lib bundle — install from GitHub only.

Some files are third-party ports included for convenience; see file headers for attribution.
