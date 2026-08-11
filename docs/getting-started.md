# 🚀 Getting started

This page is a **router** for the main pydisplay workflows. In every case, the underlying pattern is the same: connect to a display backend through ``board_config``, draw to the frame buffer, subscribe to input events, and keep the runtime alive.

## Try without installing

| Path | Guide |
|------|-------|
| Browser demo | [Try pydisplay → PyScript](try/index.md#pyscript-browser) |
| Wokwi simulator | [Try pydisplay → Wokwi](try/index.md#wokwi-simulator) |

## Quick start (install locally)

| I have… | Start here |
|---------|------------|
| ESP32 or other MicroPython board | [ESP32 board guide](guides/esp32-board.md) |
| Linux / macOS / Windows desktop | [Desktop CPython](guides/desktop-cpython.md) |
| Browser + local PyScript dev | [PyScript guide](guides/pyscript.md) |
| Wokwi only (no local install) | [Wokwi guide](guides/wokwi.md) |
| CircuitPython board | [CircuitPython platform](platforms/circuitpython.md) |
| Jupyter notebook | [Jupyter platform](platforms/jupyter.md) · [Run interactively](platforms/jupyter-run.md) |

## Learn the model

- [**App starter**](examples/app-starter.md) — copy-paste template for your first app (display, clicks, main loop)
- [**pydisplay_demo**](examples/pydisplay_demo.md) — feature tour (rotation, scrolling, buffered text, multimer)
- [Architecture](concepts/architecture.md) — how ``board_config``, ``displaydev``, and ``eventsys`` fit together
- [Portability & platforms](platforms/index.md) — where pydisplay runs and how the backend is chosen
- [Ecosystem & sister projects](ecosystem.md) — LVGL in Python, GUIs, Jupyter
- [Installation overview](installation/index.md) — MIP vs full clone vs TestPyPI / micropython-lib

A simple app usually follows this shape:

```python
from board_config import display_drv, runtime

# draw once or on each refresh
# runtime.on(...)
runtime.run_forever()
```

## Reference

- [Examples catalog](examples/index.md)
- [API reference (core)](reference/)
- [Troubleshooting](troubleshooting.md)
