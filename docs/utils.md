# Utils

Optional extensions in [`lib/utils/`](https://github.com/PyDevices/pydevices-examples/tree/main/lib/utils/). Not required for basic display and event use. API docs: [Utils Reference](reference/utils/).

Example helpers `keypins`, `wifi`, and the optional source-only
`viper_tools` accelerator live here. Product-owned desktop modules such as
`mip`, the `micropython` shim, and `frame_recorder` live in
[pydevices `utils/`](https://github.com/PyDevices/pydevices/tree/main/utils)
and are installed by `pydevices-desktop`. A sibling checkout is on `sys.path`
via [`path.py`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/utils/path.py)
during source-tree development.

## Install

```python
import mip
mip.install("github:PyDevices/pydevices-examples/packages/utils.json", target="./utils")
```

## Path setup

Preferred: set `PYTHONPATH` (CPython/CircuitPython) or `MICROPYPATH` (MicroPython) to `.:lib:utils` and run from `lib/` — no import needed.

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
| `keypins.py` | Present key events as pin-like objects |
| `wifi.py` | MicroPython `network.WLAN` shim used by examples |
| `viper_tools.py` | Optional MicroPython Viper accelerators for example utilities |
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

Many examples in `lib/examples/` depend on utils. They are excluded from the MIP packages — install from GitHub only.

Some files are third-party ports included for convenience; see file headers for attribution.
