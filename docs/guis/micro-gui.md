# Micro-GUI

[micropython-micro-gui](https://github.com/peterhinch/micropython-micro-gui) by Peter Hinch — callback-style widgets with button / encoder input (asyncio under the hood).

## Requirements

| Component | Location | Notes |
|-----------|----------|-------|
| `board_config.py` | `pydevices/board_configs/` | display + neutral input capabilities |
| `hardware_setup.py` | `lib/utils/` | Fetches micro-gui; uses `eventsys.Runtime` devices to build `Display` |
| `fetch_ph_gui.py` | `lib/utils/` | mip install into `utils/gui/` + FrameBuffer patches |
| `displaybuf.py` | `lib/utils/` | `ssd` framebuffer |
| `uctypes.py` | `lib/utils/` | CircuitPython shim for `writer.py` |

Do **not** install Peter Hinch's `drivers/`; pydevices-examples supplies the display.

## Config

Importing [`hardware_setup.py`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/utils/hardware_setup.py) calls `fetch_ph_gui("micropython-micro-gui")` then creates `ssd` and `display`. Desktop navigation defaults:

| Key | Action |
|-----|--------|
| Tab / Right | next control |
| Left | previous control |
| Enter / Space | select |
| Up / Down | increase / decrease |

## Install

```python
import mip
mip.install("github:PyDevices/pydevices-examples/packages/micropython-micro-gui.json", target="./utils")
```

Or rely on `import hardware_setup` (needs `mip` on the target when `gui/` is missing).

## Example

[`lib/examples/micro_gui_simpletest.py`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/examples/micro_gui_simpletest.py) — framebuffer smoke test. Full demos: `import hardware_setup` then `import gui.demos.simple`.

Browser: `fetch_ph_gui` via `hardware_setup` — [gallery loader](https://PyDevices.github.io/pydevices-examples/pyscript/micropython.html?modules=micro_gui_simpletest).

## See also

- [Nano-GUI](nano-gui.md)
- [MicroPython-Touch](micropython-touch.md)
