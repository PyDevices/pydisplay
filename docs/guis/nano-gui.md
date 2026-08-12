# Nano-GUI

[Nano-GUI](https://github.com/peterhinch/micropython-nano-gui) by Peter Hinch — lightweight GUI for memory-constrained MicroPython boards.

pydevices-examples does **not** vendor Nano-GUI in the git repo. [`color_setup.py`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/utils/color_setup.py) calls [`fetch_ph_gui`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/utils/fetch_ph_gui.py) to install the `gui/` tree into `utils/` and patch `pygraphics.FrameBuffer` isinstance checks. Display wiring uses [`displaybuf.py`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/utils/displaybuf.py).

## Requirements

| Component | Location | Notes |
|-----------|----------|-------|
| `board_config.py` | `pydevices/board_configs/` | display and neutral touch setup |
| `color_setup.py` | `lib/utils/` | Ships with pydevices-examples — fetches nano-gui, creates `ssd` |
| `fetch_ph_gui.py` | `lib/utils/` | mip install + FrameBuffer patches |
| `gui/` | `lib/utils/gui/` | **Upstream** — installed by fetch (not in git) |
| `uctypes.py` | `lib/utils/` | CircuitPython shim for nano-gui `writer.py` |
| `utils.path` | `lib/utils/path.py` | Dev clone — puts `utils/` on `sys.path` |

Peter Hinch's `drivers/` tree is for bare-metal MCU displays. With pydevices-examples you use `color_setup.ssd` instead; you do **not** need `drivers/`.

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
mip.install("github:PyDevices/pydevices-examples/packages/micropython-nano-gui.json", target="./utils")
```

`lib/utils/gui/` is gitignored. Only one Hinch GUI may occupy `utils/gui/` at a time; `fetch_ph_gui` empties the directory when switching.

## Example

[`lib/examples/nano_gui_simpletest.py`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/examples/nano_gui_simpletest.py) — hardware verification from the [upstream docs](https://github.com/peterhinch/micropython-nano-gui#23-verifying-hardware-configuration).

Browser gallery: no special header — `color_setup` calls `fetch_ph_gui("micropython-nano-gui")` ([live loader](https://PyDevices.github.io/pydevices-examples/pyscript/micropython.html?modules=nano_gui_simpletest)).

```bash
cd pydevices-examples/lib
micropython -i utils/path.py examples/nano_gui_simpletest.py
```

## See also

- [Micro-GUI](micro-gui.md) — buttons / encoder
- [MicroPython-Touch](micropython-touch.md) — touch widgets
- [Config files](../concepts/config-files.md)
