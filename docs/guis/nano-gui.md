# Nano-GUI

[Nano-GUI](https://github.com/peterhinch/micropython-nano-gui) by Peter Hinch — lightweight GUI for memory-constrained MicroPython boards.

pydisplay does **not** vendor Nano-GUI in the git repo. [`color_setup.py`](https://github.com/PyDevices/pydisplay/blob/main/src/utils/color_setup.py) calls [`fetch_ph_gui`](https://github.com/PyDevices/pydisplay/blob/main/src/utils/fetch_ph_gui.py) to install the `gui/` tree into `utils/` and patch `pygraphics.FrameBuffer` isinstance checks. Display wiring uses [`displaybuf.py`](https://github.com/PyDevices/pydisplay/blob/main/src/utils/displaybuf.py).

## Requirements

| Component | Location | Notes |
|-----------|----------|-------|
| `board_config.py` | `micropython-hardware/board_configs/` | display and neutral touch setup |
| `color_setup.py` | `src/utils/` | Ships with pydisplay — fetches nano-gui, creates `ssd` |
| `fetch_ph_gui.py` | `src/utils/` | mip install + FrameBuffer patches |
| `gui/` | `src/utils/gui/` | **Upstream** — installed by fetch (not in git) |
| `uctypes.py` | `src/utils/` | CircuitPython shim for nano-gui `writer.py` |
| `utils.path` | `src/utils/path.py` | Dev clone — puts `utils/` on `sys.path` |

Peter Hinch's `drivers/` tree is for bare-metal MCU displays. With pydisplay you use `color_setup.ssd` instead; you do **not** need `drivers/`.

## Install the `gui` package

Usually you do not install manually — importing `color_setup` runs `fetch_ph_gui("micropython-nano-gui")`.

### Full clone (development)

```bash
curl -sL https://github.com/peterhinch/micropython-nano-gui/archive/refs/heads/master.tar.gz \
  | tar xz --strip-components=2 -C src/utils micropython-nano-gui-master/gui
```

Or via mip / our full package manifest:

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/micropython-nano-gui.json", target="./utils")
```

`src/utils/gui/` is gitignored. Only one Hinch GUI may occupy `utils/gui/` at a time; `fetch_ph_gui` empties the directory when switching.

## Example

[`src/examples/nano_gui_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/nano_gui_simpletest.py) — hardware verification from the [upstream docs](https://github.com/peterhinch/micropython-nano-gui#23-verifying-hardware-configuration).

Browser gallery: no special header — `color_setup` calls `fetch_ph_gui("micropython-nano-gui")` ([live loader](https://PyDevices.github.io/pydisplay/pyscript/micropython.html?modules=nano_gui_simpletest)).

```bash
cd pydisplay/src
micropython -i utils/path.py examples/nano_gui_simpletest.py
```

## See also

- [Micro-GUI](micro-gui.md) — buttons / encoder
- [MicroPython-Touch](micropython-touch.md) — touch widgets
- [Config files](../concepts/config-files.md)
