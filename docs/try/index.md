# Try pydisplay

Evaluate pydisplay without installing anything on your machine.

## Choose a demo

| Path | Best for | Start here |
|------|----------|------------|
| **Browser (PyScript)** | Quick look, touch UI in the tab | [Live demo hub](https://PyDevices.github.io/pydisplay/pyscript/) |
| **Wokwi simulator** | ESP32 + ILI9341 without hardware | [Wokwi guide](../guides/wokwi.md) · [`wokwi/`](../sim/wokwi/) |
| **Screenshot gallery** | See what examples look like | [Gallery below](#screenshot-gallery) |

## PyScript (browser)

### Live demo (online)

**Hub:** [PyDevices.github.io/pydisplay/pyscript/](https://PyDevices.github.io/pydisplay/pyscript/)

| Link | Description |
|------|-------------|
| [Calculator](https://PyDevices.github.io/pydisplay/pyscript/load.html?modules=calculator) | Async calculator |
| [Test runner](https://PyDevices.github.io/pydisplay/pyscript/test.html) | Pick an example |
| [REPL](https://PyDevices.github.io/pydisplay/pyscript/repl.html) | Interactive REPL + canvas |
| [Editor](https://PyDevices.github.io/pydisplay/pyscript/editor.html) | mpy-editor with paint.py |

### Run locally

--8<-- "_snippets/pyscript-local.md"

Full guide (asyncio porting, compatible examples, board config): [PyScript local development](../guides/pyscript.md).

!!! note "Browser gallery"
    The [live demo hub](https://PyDevices.github.io/pydisplay/pyscript/) lists examples tagged `# multimer types: async` or `all`. Click **Run** on each page — blocking loops start only after Run. Async examples (`calculator`, `paint`, …) are the smoothest fit. See [PyScript asyncio guide](../guides/pyscript-asyncio.md).

## Wokwi (simulator)

Copy [`wokwi/`](../sim/wokwi/) `main.py` and `diagram.json` into a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micropython-esp32-s3).

Full example catalog: uncomment the two `add_ons` / `examples` lines in `main.py` (see [Wokwi guide](../guides/wokwi.md)).

## Screenshot gallery

| | | |
|--|--|--|
| ![active](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/active.gif) | ![tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/tiny_toasters.gif) | ![calculator](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/calculator.png) |
| ![color_test](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/color_test.png) | ![console_advanced_demo](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/console_advanced_demo.gif) | ![paint](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/paint.png) |
| ![circuitpython_usb_video](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/circuitpython_usb_video_chromebook.gif) | ![proverbs](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/proverbs.png) | ![testris](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/testris.png) |

Full table: [assets/screenshots/README.md](https://github.com/PyDevices/pydisplay/blob/main/assets/screenshots/README.md).

## Next steps

Ready to install locally?

- [ESP32 / MicroPython board](../guides/esp32-board.md)
- [Desktop CPython](../guides/desktop-cpython.md)
- [PyScript local dev](../guides/pyscript.md)
- [Installation overview](../installation/index.md)
