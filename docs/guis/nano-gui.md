# Nano-GUI

[Nano-GUI](https://github.com/peterhinch/micropython-nano-gui) by Peter Hinch — lightweight GUI for memory-constrained MicroPython boards.

pydisplay does **not** vendor Nano-GUI in the git repo. [`color_setup.py`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/color_setup.py) calls [`fetch_ph_gui`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/fetch_ph_gui.py) to install the `gui/` tree into `add_ons/` and patch `graphics.FrameBuffer` isinstance checks. Display wiring uses [`displaybuf.py`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/displaybuf.py).

## Requirements

| Component | Location | Notes |
|-----------|----------|-------|
| `board_config.py` | `board_configs/` or `src/lib/` | pydisplay display and touch setup |
| `color_setup.py` | `src/add_ons/` | Ships with pydisplay — fetches nano-gui, creates `ssd` |
| `fetch_ph_gui.py` | `src/add_ons/` | mip install + FrameBuffer patches |
| `gui/` | `src/add_ons/gui/` | **Upstream** — installed by fetch (not in git) |
| `uctypes.py` | `src/add_ons/` | CircuitPython shim for nano-gui `writer.py` |
| `lib.path` | `src/lib/path.py` | Dev clone — puts `add_ons/` on `sys.path` |

Peter Hinch's `drivers/` tree is for bare-metal MCU displays. With pydisplay you use `color_setup.ssd` instead; you do **not** need `drivers/`.

## Install the `gui` package

Usually you do not install manually — importing `color_setup` runs `fetch_ph_gui("micropython-nano-gui")`.

### Full clone (development)

```bash
curl -sL https://github.com/peterhinch/micropython-nano-gui/archive/refs/heads/master.tar.gz \
  | tar xz --strip-components=2 -C src/add_ons micropython-nano-gui-master/gui
```

Or via mip / our full package manifest:

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/micropython-nano-gui.json", target="./add_ons")
```

`src/add_ons/gui/` is gitignored. Only one Hinch GUI may occupy `add_ons/gui/` at a time; `fetch_ph_gui` empties the directory when switching.

## Example

[`src/examples/nano_gui_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/nano_gui_simpletest.py) — hardware verification from the [upstream docs](https://github.com/peterhinch/micropython-nano-gui#23-verifying-hardware-configuration).

Browser gallery: mark with `# pyscript packages: micropython-nano-gui` so [PyScript](../guides/pyscript.md) pre-installs `gui/` before import ([live loader](https://PyDevices.github.io/pydisplay/pyscript/load.html?modules=nano_gui_simpletest&packages=micropython-nano-gui)).

```bash
cd pydisplay/src
micropython -i lib/path.py examples/nano_gui_simpletest.py
```

## See also

- [Micro-GUI](micro-gui.md) — buttons / encoder
- [MicroPython-Touch](micropython-touch.md) — touch widgets
- [Config files](../concepts/config-files.md)
