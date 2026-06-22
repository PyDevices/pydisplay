# Nano-GUI

[Nano-GUI](https://github.com/peterhinch/micropython-nano-gui) by Peter Hinch — lightweight GUI for memory-constrained MicroPython boards.

pydisplay does **not** vendor Nano-GUI in the git repo. You install Peter Hinch's `gui` tree locally (see below) and wire the display through pydisplay's [`color_setup.py`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/color_setup.py) and [`displaybuf.py`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/displaybuf.py).

## Requirements

| Component | Location | Notes |
|-----------|----------|-------|
| `board_config.py` | `board_configs/` or `src/lib/` | pydisplay display and touch setup |
| `color_setup.py` | `src/add_ons/` | Ships with pydisplay — creates `ssd` via DisplayBuffer |
| `gui/` | `src/add_ons/gui/` | **Upstream** — copy from [micropython-nano-gui](https://github.com/peterhinch/micropython-nano-gui) |
| `lib.path` | `src/lib/path.py` | Dev clone — puts `add_ons/` on `sys.path` so `import gui` works |

Peter Hinch's `drivers/` tree is for bare-metal MCU displays. With pydisplay you use `color_setup.ssd` instead; you do **not** need `drivers/` for the pydisplay examples.

## Install the `gui` package

### Full clone (development)

From the pydisplay repo root, copy only the `gui` directory into `add_ons/`:

```bash
curl -sL https://github.com/peterhinch/micropython-nano-gui/archive/refs/heads/master.tar.gz \
  | tar xz --strip-components=2 -C src/add_ons micropython-nano-gui-master/gui
```

`src/add_ons/gui/` is listed in [`.gitignore`](https://github.com/PyDevices/pydisplay/blob/main/.gitignore) — it is a local upstream checkout, not part of the pydisplay tree.

Expected layout:

```
src/add_ons/
├── color_setup.py      # pydisplay — wires board_config → DisplayBuffer
├── displaybuf.py
└── gui/                # Peter Hinch — not in git
    ├── core/
    ├── fonts/
    ├── widgets/
    └── demos/
```

Because [`path.py`](https://github.com/PyDevices/pydisplay/blob/main/src/lib/path.py) adds `add_ons/` to `sys.path`, imports match upstream Nano-GUI:

```python
from color_setup import ssd
from gui.core.colors import RED, BLUE, GREEN
from gui.core.nanogui import refresh
```

### MicroPython device (MIP)

On hardware, install Nano-GUI into the same directory as `color_setup.py` (typically `./add_ons` or `/lib`):

```python
import mip
mip.install("github:peterhinch/micropython-nano-gui", target="./add_ons")
mip.install("github:PyDevices/pydisplay/packages/add_ons.json", target="./add_ons")
```

Adjust `target=` so `gui/` and `color_setup.py` sit in the same path root.

## Example

[`src/examples/nano_gui_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/nano_gui_simpletest.py) — hardware verification script from the [upstream Nano-GUI docs](https://github.com/peterhinch/micropython-nano-gui#23-verifying-hardware-configuration).

Run from a full clone:

```bash
cd pydisplay/src
micropython -i lib/path.py examples/nano_gui_simpletest.py
```

Desktop CPython / MicroPython unix also work when `board_config` provides an SDL or PG display.

Tagged `# multimer types: all` in the [examples catalog](../examples/index.md#multimer-portability-markers).

## Platform

MicroPython and CPython (via pydisplay `displaybuf` + desktop `board_config`). Not CircuitPython or PyScript.

## See also

- [Config files](../concepts/config-files.md) — `color_setup.py` and add-on layout
- [Add-ons](../add-ons.md) — `displaybuf.py` and pydisplay add-on packages
- [Drawing and fonts](../concepts/drawing-and-fonts.md) — DisplayBuffer overview
