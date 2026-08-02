# MicroPython-Touch

[micropython-touch](https://github.com/peterhinch/micropython-touch) by Peter Hinch — touch widgets and async UI (developed from micro-gui).

## Requirements

| Component | Location | Notes |
|-----------|----------|-------|
| `board_config.py` | `board_configs/` or `src/lib/` | display + `eventsys.Runtime` |
| `touch_setup.py` | `src/utils/` | Fetches touch GUI; mouse/touch `Poller` → `Display(ssd, tpad)` |
| `fetch_ph_gui.py` | `src/utils/` | mip install into `utils/gui/` + FrameBuffer patches |
| `displaybuf.py` | `src/utils/` | `ssd` framebuffer |
| `uctypes.py` | `src/utils/` | CircuitPython shim for `writer.py` |

Upstream renamed `hardware_setup.py` → `touch_setup.py` (Dec 2024). pydisplay follows that name. Do **not** install upstream `drivers/` or `touch/` packages for the pydisplay bridge — input comes from `eventsys`.

## Config

```python
import touch_setup  # fetch + Display
from gui.core.tgui import Screen, ssd
```

## Install

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/micropython-touch.json", target="./utils")
```

Or rely on `import touch_setup`.

## Example

[`src/examples/touch_gui_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/touch_gui_simpletest.py) — framebuffer smoke test. Full demos: `import touch_setup` then `import gui.demos.simple`.

Browser: `fetch_ph_gui` via `touch_setup` — [gallery loader](https://PyDevices.github.io/pydisplay/pyscript/micropython.html?modules=touch_gui_simpletest).

## See also

- [Nano-GUI](nano-gui.md)
- [Micro-GUI](micro-gui.md)
