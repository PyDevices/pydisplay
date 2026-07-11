# Micro-GUI

[micropython-micro-gui](https://github.com/peterhinch/micropython-micro-gui) by Peter Hinch — callback-style widgets with button / encoder input (asyncio under the hood).

## Requirements

| Component | Location | Notes |
|-----------|----------|-------|
| `board_config.py` | `board_configs/` or `src/lib/` | display + `eventsys.Runtime` |
| `hardware_setup.py` | `src/add_ons/` | Fetches micro-gui; builds `Display` with keyboard stand-ins on desktop |
| `fetch_ph_gui.py` | `src/add_ons/` | mip install into `add_ons/gui/` + FrameBuffer patches |
| `displaybuf.py` | `src/add_ons/` | `ssd` framebuffer |
| `uctypes.py` | `src/add_ons/` | CircuitPython shim for `writer.py` |

Do **not** install Peter Hinch's `drivers/`; pydisplay supplies the display.

## Config

Importing [`hardware_setup.py`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/hardware_setup.py) calls `fetch_ph_gui("micropython-micro-gui")` then creates `ssd` and `display`. Desktop navigation defaults:

| Key | Action |
|-----|--------|
| Tab / Right | next control |
| Left | previous control |
| Enter / Space | select |
| Up / Down | increase / decrease |

## Install

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/micropython-micro-gui.json", target="./add_ons")
```

Or rely on `import hardware_setup` (needs `mip` on the target when `gui/` is missing).

## Example

[`src/examples/micro_gui_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/micro_gui_simpletest.py) — framebuffer smoke test. Full demos: `import hardware_setup` then `import gui.demos.simple`.

Browser: `# pyscript packages: micropython-micro-gui` — [gallery loader](https://PyDevices.github.io/pydisplay/pyscript/load.html?modules=micro_gui_simpletest&packages=micropython-micro-gui).

## See also

- [Nano-GUI](nano-gui.md)
- [MicroPython-Touch](micropython-touch.md)
