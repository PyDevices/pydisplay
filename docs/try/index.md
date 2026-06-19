# Try pydisplay

Evaluate pydisplay without installing anything on your machine.

## Choose a demo

| Path | Best for | Start here |
|------|----------|------------|
| **Browser (PyScript)** | Quick look, touch UI in the tab | [Live demo hub](https://PyDevices.github.io/pydisplay/demo/) |
| **Wokwi simulator** | ESP32 + ILI9341 without hardware | [Minimum project guide](../guides/wokwi.md) or [hosted copy](https://wokwi.com/projects/404248867674669057) |
| **Screenshot gallery** | See what examples look like | [Gallery below](#screenshot-gallery) |

## PyScript (browser)

### Live demo (online)

**Hub:** [PyDevices.github.io/pydisplay/demo/](https://PyDevices.github.io/pydisplay/demo/)

| Link | Description |
|------|-------------|
| [Calculator](https://PyDevices.github.io/pydisplay/demo/html/example.html?script=calculator) | Async calculator |
| [Test runner](https://PyDevices.github.io/pydisplay/demo/html/test.html) | Pick an example |
| [REPL](https://PyDevices.github.io/pydisplay/demo/html/repl.html) | Interactive REPL + canvas |
| [Editor](https://PyDevices.github.io/pydisplay/demo/html/editor.html) | mpy-editor with paint.py |

### Run locally

--8<-- "_snippets/pyscript-local.md"

Full guide (asyncio porting, compatible examples, board config): [PyScript local development](../guides/pyscript.md).

!!! note
    Most examples use blocking loops and **will not run** in PyScript until ported to asyncio. See [PyScript asyncio guide](../guides/pyscript-asyncio.md).

## Wokwi (simulator)

Copy [`wokwi/minimum/`](https://github.com/PyDevices/pydisplay/tree/main/wokwi/minimum) into a [new ESP32-S3 MicroPython project](https://wokwi.com/projects/new/micropython-esp32-s3), or open the [hosted minimum project](https://wokwi.com/projects/404248867674669057).

Full install with examples: [`wokwi/esp32-s3-full/`](https://github.com/PyDevices/pydisplay/tree/main/wokwi/esp32-s3-full) ([hosted copy](https://wokwi.com/projects/415770470006384641)).

Details: [Wokwi guide](../guides/wokwi.md).

## Screenshot gallery

| | | |
|--|--|--|
| ![active](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/active.gif) | ![tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/tiny_toasters.gif) | ![calculator](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/calculator.png) |
| ![color_test](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/color_test.png) | ![console_advanced_demo](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/console_advanced_demo.gif) | ![paint](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/paint.png) |
| ![circuitpython_usb_video](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/circuitpython_usb_video_chromebook.gif) | ![proverbs](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/proverbs.png) | ![testris](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/testris.png) |

Full table: [screenshots/README.md](https://github.com/PyDevices/pydisplay/blob/main/screenshots/README.md).

## Next steps

Ready to install locally?

- [ESP32 / MicroPython board](../guides/esp32-board.md)
- [Desktop CPython](../guides/desktop-cpython.md)
- [PyScript local dev](../guides/pyscript.md)
- [Installation overview](../installation/index.md)
