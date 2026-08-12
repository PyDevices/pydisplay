# Utils

Optional extensions in [`src/utils/`](https://github.com/PyDevices/pydevices-examples/tree/main/src/utils/). Not required for basic display and event use. API docs: [Utils Reference](reference/utils/).

MCU / host helpers that used to live here (`byteswap`, `viper_tools`, `mip`,
`micropython` shim, `keypins`, `wifi`, `frame_recorder`) are in
[pydevices `utils/`](https://github.com/PyDevices/pydevices/tree/main/utils).
`packages/utils.json` depends on that tree; a sibling checkout is on
`sys.path` via [`path.py`](https://github.com/PyDevices/pydevices-examples/blob/main/src/utils/path.py).

## Install

```python
import mip
mip.install("github:PyDevices/pydevices-examples/packages/utils.json", target="./utils")
```

## Path setup

Preferred: set `PYTHONPATH` (CPython/CircuitPython) or `MICROPYPATH` (MicroPython) to `.:lib:utils` and run from `src/` — no import needed.

When environment variables are unavailable or not set as recommended (for example, a bare device REPL, or `boot.py`/`main.py`), put `lib/` and `utils/` on `sys.path` explicitly:

```python
import utils.path
```

Or copy the utils modules into `lib/` on your device.

## Notable modules

| Module | Purpose |
|--------|---------|
| `framebuf.py` | framebuf API on CPython/CircuitPython |
| `displaybuf.py` | Peter Hinch DisplayBuffer API |
| `console.py` | Terminal-style console widget |
| `lv_encoder_emu.py` | Desktop-only soft encoder UI on a secondary surface (stand-in for MCU `machine.Encoder` / `rotaryio`); see `examples/lv_multi_display.py` |
| `pdwidgets/` | Moved to [pdwidgets](https://github.com/PyDevices/pdwidgets) — [user guide](guis/pywidgets.md) |
| `palettes/` | Moved to [palettes](https://github.com/PyDevices/palettes) — [user guide](guis/palettes.md) |
| `tft_text.py`, `tft_write.py` | russhughes font rendering |
| `png.py` | PNG support (experimental) |

Third-party trees copied locally (not in `utils.json`):

| Path | Purpose |
|------|---------|
| `gui/` | Peter Hinch GUIs — install via [`fetch_ph_gui`](guis/nano-gui.md); gitignored; one of nano / micro / touch at a time |

Many examples in `src/examples/` depend on utils. They are excluded from the micropython-lib packages — install from GitHub only.

Some files are third-party ports included for convenience; see file headers for attribution.
