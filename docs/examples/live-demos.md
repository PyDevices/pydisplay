# Live demos

Try pydisplay without installing locally.

## PyScript (browser)

**URL:** [PyDevices.github.io/pydisplay/demo/](https://PyDevices.github.io/pydisplay/demo/)

| Link | Description |
|------|-------------|
| [Calculator](https://PyDevices.github.io/pydisplay/demo/html/example.html?script=calculator) | Async calculator example |
| [Test runner](https://PyDevices.github.io/pydisplay/demo/html/test.html) | Pick an example |
| [REPL](https://PyDevices.github.io/pydisplay/demo/html/repl.html) | Interactive REPL + canvas |
| [Editor](https://PyDevices.github.io/pydisplay/demo/html/editor.html) | mpy-editor with paint.py |

Local: `python -m http.server` from repo root — see [PyScript platform guide](../platforms/pyscript.md).

!!! note
    Most examples are not asyncio-compatible and won't run in PyScript. Only a subset works in the browser.

## Wokwi (simulator)

| Project | Description |
|---------|-------------|
| [ESP32-S3 full example](https://wokwi.com/projects/415770470006384641) | installer.py + pydisplay |
| [Minimum config](https://wokwi.com/projects/404248867674669057) | displaysys + eventsys only |

Details: [Wokwi hardware guide](../hardware/wokwi.md).

## Screenshot gallery

Examples with captured output in [`screenshots/`](https://github.com/PyDevices/pydisplay/tree/main/screenshots):

| | | |
|--|--|--|
| ![active](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/active.gif) | ![tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/tiny_toasters.gif) | ![calculator](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/calculator.png) |
| ![color_test](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/color_test.png) | ![console_advanced_demo](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/console_advanced_demo.gif) | ![paint](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/paint.png) |
| ![circuitpython_usb_video](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/circuitpython_usb_video_chromebook.gif) | ![proverbs](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/proverbs.png) | ![testris](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/testris.png) |

Full table: [screenshots/README.md](https://github.com/PyDevices/pydisplay/blob/main/screenshots/README.md).
