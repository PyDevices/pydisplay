# Getting started

The fastest way to try pydisplay depends on your platform.

## TL;DR

1. **Desktop (CPython or MicroPython on Unix)** — clone the repo, `cd src`, run `python3 -i path.py`, then `import hello`.
2. **MicroPython on a board** — install packages with [installer.py](installation/installer.md) or `mip`, pick a [board config](hardware/board-configs.md), then run an example.
3. **Browser (PyScript)** — open the [live demo](https://PyDevices.github.io/pydisplay/demo/) or run `python -m http.server` from the repo root.
4. **Wokwi simulator** — copy [`wokwi/minimum/`](https://github.com/PyDevices/pydisplay/tree/main/wokwi/minimum) into a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micro-python-esp32-s3), or open the [hosted example](https://wokwi.com/projects/415770470006384641).

## Choose an install method

| Method | Best for | Details |
|--------|----------|---------|
| [Full clone](installation/full-clone.md) | Development, all examples | `git clone` + `import lib.path` |
| [GitHub MIP](installation/mip-github.md) | MicroPython devices, source `.py` files | `packages/*.json`, board configs |
| [micropython-lib MIP](installation/mip-micropython-lib.md) | MicroPython devices, precompiled `.mpy` | PyDevices package index |
| [installer.py](installation/installer.md) | One-shot setup on a device | Combines both MIP sources |

PyPI wheels are not published for end users yet. TestPyPI uploads exist for maintainer testing only.

## Run your first example

Every example expects `path.py` to be imported first (unless you installed everything into `lib/` on the device).

```python
import lib.path   # or: import path  (desktop clone layout)
import hello       # any script from src/examples/
```

On desktop from a full clone:

```bash
cd src
python3 -i path.py
```

Then at the `>>>` prompt: `import hello`.

On a microcontroller with `mpremote`:

```bash
mpremote mount .
# at REPL:
import lib.path
import hello
```

See [platform-specific guides](platforms/micropython.md) for SDL2/PyGame setup on desktop, CircuitPython copying, Jupyter, and PyScript.

## Minimum packages

For LVGL or framebuffer-only use without the full bundle:

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/displaysys.json")
mip.install("github:PyDevices/pydisplay/packages/eventsys.json")
mip.install("github:PyDevices/pydisplay/board_configs/<your_board>")
```

See the [minimum Wokwi project](https://github.com/PyDevices/pydisplay/tree/main/wokwi/minimum) ([hosted copy](https://wokwi.com/projects/404248867674669057)) for a working example.

## Next steps

- [Installation overview](installation/index.md) — all three install channels explained
- [Board configs](hardware/board-configs.md) — pick hardware settings
- [Examples catalog](examples/index.md) — what to run after hello
- [Concepts: displays](concepts/displays.md) — BusDisplay, SDL2Display, and friends
