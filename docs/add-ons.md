# Add-ons

Optional extensions in [`src/add_ons/`](https://github.com/PyDevices/pydisplay/tree/main/src/add_ons/). Not required for basic display and event use. API docs: [Add-ons Reference](reference/add_ons/).

## Install

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/add_ons.json", target="./add_ons")
```

## Path setup

In a development clone, put `lib/`, `add_ons/`, and `examples/` on `sys.path`:

```python
import lib.path
```

Or copy the add-on modules into `lib/` on your device.

## Notable modules

| Module | Purpose |
|--------|---------|
| `framebuf.py` | framebuf API on CPython/CircuitPython |
| `displaybuf.py` | Peter Hinch DisplayBuffer API |
| `console.py` | Terminal-style console widget |
| `pdwidgets/` | Moved to [pdwidgets](https://github.com/PyDevices/pdwidgets) — [user guide](guis/pywidgets.md) |
| `palettes/` | Moved to [palettes](https://github.com/PyDevices/palettes) — [user guide](guis/palettes.md) |
| `tft_text.py`, `tft_write.py` | russhughes font rendering |
| `png.py` | PNG support (experimental) |

Third-party trees copied locally (not in `add_ons.json`):

| Path | Purpose |
|------|---------|
| `gui/` | Peter Hinch GUIs — install via [`fetch_ph_gui`](guis/nano-gui.md); gitignored; one of nano / micro / touch at a time |

Many examples in `src/examples/` depend on add_ons. They are excluded from the micropython-lib packages — install from GitHub only.

Some files are third-party ports included for convenience; see file headers for attribution.
