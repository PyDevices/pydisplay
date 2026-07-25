# Hardware setup

Board configs, drivers, and the board-devices contract docs live in
**[micropython-hardware](https://github.com/PyDevices/micropython-hardware)**
and are published on GitHub Pages (markdown → HTML, not Read the Docs):

**[pydevices.github.io/micropython-hardware](https://pydevices.github.io/micropython-hardware/)**

| Topic | Page |
|-------|------|
| Board configs | [board-configs](https://pydevices.github.io/micropython-hardware/board-configs.html) |
| Board devices contract | [board-devices](https://pydevices.github.io/micropython-hardware/board-devices.html) |
| Display / touch drivers | [display-drivers](https://pydevices.github.io/micropython-hardware/display-drivers.html), [touch-drivers](https://pydevices.github.io/micropython-hardware/touch-drivers.html) |
| Device matrix | [device-matrix](https://pydevices.github.io/micropython-hardware/device-matrix.html) |

pydisplay still documents how apps use those boards:

- [Runtime](../concepts/runtime.md) — `display_drv` / `runtime` / touch read
- [Config files](../concepts/config-files.md) — `board_config.py` and add-on templates
