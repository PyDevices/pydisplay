# 🚀 Try pydevices-examples

Evaluate pydevices-examples without installing anything on your machine.

## Choose a demo

| Path | Best for | Start here |
|------|----------|------------|
| **Browser (PyScript)** | Quick look, touch UI in the tab | [Live demo hub](https://PyDevices.github.io/pydevices-examples/pyscript/) |
| **Installable PWA** | Home-screen / standalone app on phone or desktop | [Where PWAs run](../platforms/pwa.md) · [Install the gallery](https://PyDevices.github.io/pydevices-examples/pyscript/) |
| **Wokwi simulator** | ESP32 + ILI9341 without hardware | [Wokwi guide](../guides/wokwi.md) · [`wokwi/`](../../web/wokwi/) |
| **Screenshot gallery** | See what examples look like | [Gallery below](#screenshot-gallery) |

## PyScript (browser)

### Live demo (online)

**Hub:** [PyDevices.github.io/pydevices-examples/pyscript/](https://PyDevices.github.io/pydevices-examples/pyscript/) — also an installable [PWA](../platforms/pwa.md) (**Install app** in the header on Chromium; on iOS use Share → Add to Home Screen).

| Link | Description |
|------|-------------|
| [Calculator](https://PyDevices.github.io/pydevices-examples/pyscript/micropython.html?modules=calc_graphics,calc_engine) | Pocket calculator (graphics) |
| [REPL](https://PyDevices.github.io/pydevices-examples/pyscript/repl.html) | Interactive REPL + canvas |
| [Editor](https://PyDevices.github.io/pydevices-examples/pyscript/editor.html) | `mpy-editor` with hidden `setup` + editable lesson |
| [Async](https://PyDevices.github.io/pydevices-examples/pyscript/async.html) | Non-blocking animation with `await` |
| [DOM](https://PyDevices.github.io/pydevices-examples/pyscript/dom.html) | HTML button → Python via `create_proxy` |
| [Pyodide](https://PyDevices.github.io/pydevices-examples/pyscript/pyodide.html?manifests=chango) | Modules / MIP manifests under Pyodide (dev tool) |

### Run locally

--8<-- "_snippets/pyscript-local.md"

Full guide (asyncio porting, compatible examples, board config): [PyScript local development](../guides/pyscript.md).

!!! note "Browser gallery"
    The [live demo hub](https://PyDevices.github.io/pydevices-examples/pyscript/) lists every example entry by default (opt out with `# gallery: skip`). Click **Run** on each page. Prefer `runtime.run_forever()` with callbacks so demos stay responsive. See [PyScript asyncio guide](../guides/pyscript-asyncio.md).

## Wokwi (simulator)

Copy [`wokwi/`](../../web/wokwi/) `main.py` and `diagram.json` into a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micropython-esp32-s3).

Full example catalog: uncomment the two `utils` / `examples` lines in `main.py` (see [Wokwi guide](../guides/wokwi.md)).

## Screenshot gallery

| | |
|--|--|
| ![tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydevices-examples/main/docs/screenshots/tiny_toasters.gif) | ![paint](https://raw.githubusercontent.com/PyDevices/pydevices-examples/main/docs/screenshots/paint.png) |

Full gallery (all screenshots): [docs/screenshots/README.md](../screenshots/README.md).

## Next steps

Ready to install locally?

- [ESP32 / MicroPython board](../guides/esp32-board.md)
- [Desktop CPython](../guides/desktop-cpython.md)
- [PyScript local dev](../guides/pyscript.md)
- [Installation overview](../installation/index.md)
