# Micro-GUI

[micropython-micro-gui](https://github.com/peterhinch/micropython-micro-gui) by Peter Hinch — callback-style widgets with button / encoder input (asyncio under the hood).

## Requirements

| Component | Location | Notes |
|-----------|----------|-------|
| `board_config.py` | `board_configs/` or `src/lib/` | display + `eventsys.Runtime` |
| `hardware_setup.py` | `src/utils/` | Fetches micro-gui; builds `Display` with keyboard stand-ins on desktop |
| `fetch_ph_gui.py` | `src/utils/` | mip install into `utils/gui/` + FrameBuffer patches |
| `displaybuf.py` | `src/utils/` | `ssd` framebuffer |
| `uctypes.py` | `src/utils/` | CircuitPython shim for `writer.py` |

Do **not** install Peter Hinch's `drivers/`; pydisplay supplies the display.

## Config

Importing [`hardware_setup.py`](https://github.com/PyDevices/pydisplay/blob/main/src/utils/hardware_setup.py) calls `fetch_ph_gui("micropython-micro-gui")` then creates `ssd` and `display`. Desktop navigation defaults:

| Key | Action |
|-----|--------|
| Tab / Right | next control |
| Left | previous control |
| Enter / Space | select |
| Up / Down | increase / decrease |

## Install

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/micropython-micro-gui.json", target="./utils")
```

Or rely on `import hardware_setup` (needs `mip` on the target when `gui/` is missing).

## Example

[`src/examples/micro_gui_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/micro_gui_simpletest.py) — framebuffer smoke test. Full demos: `import hardware_setup` then `import gui.demos.simple`.

Browser: `fetch_ph_gui` via `hardware_setup` — [gallery loader](https://PyDevices.github.io/pydisplay/pyscript/micropython.html?modules=micro_gui_simpletest).

## See also

- [Nano-GUI](nano-gui.md)
- [MicroPython-Touch](micropython-touch.md)
