<h1 align="center">PyDisplay examples</h1>

<h3 align="center">See the portable PyDevices driver stack in action.</h3>

<p align="center">
  <a href="https://pydisplay.readthedocs.io">Documentation</a> •
  <a href="https://PyDevices.github.io/pydisplay/pyscript/">PyScript gallery</a> •
  <a href="https://pydevices.github.io/micropython-hardware/">Product packages</a> •
  <a href="docs/screenshots/README.md">Screenshots</a>
</p>

| ![paint.py](https://raw.githubusercontent.com/PyDevices/pydisplay/main/docs/screenshots/paint.png) | ![tiny_toasters.py](https://raw.githubusercontent.com/PyDevices/pydisplay/main/docs/screenshots/tiny_toasters.gif) |
|:--:|:--:|
| `paint.py` | `tiny_toasters.py` |

This repository is the examples, integration documentation, and browser gallery
for the PyDevices driver ecosystem. The reusable product source lives in
**[micropython-hardware](https://github.com/PyDevices/micropython-hardware)**:

- `displaydev` and `audiodev` provide portable display and audio interfaces.
- `events`, `keys`, and `multimer` provide shared event, key, and timing primitives.
- `eventsys` is an optional application traffic controller for non-LVGL apps.
- `board_configs`, `board_devices`, and hardware drivers connect those interfaces
  to real boards and desktop/browser hosts.

Those libraries are designed to work across MicroPython, CircuitPython, and
CPython on microcontrollers, Linux, Windows, Android, browsers, and notebooks.
This repo demonstrates that portability; it is not the package source of truth.

> **Alpha quality.** The organization is being prepared for its first external
> users, so names and APIs may still evolve.

## Try it

The fastest route is the installable
**[PyScript gallery](https://PyDevices.github.io/pydisplay/pyscript/)**. It runs
the real examples in a browser and can be installed as a Progressive Web App.
The [PWA guide](https://pydisplay.readthedocs.io/en/latest/guides/pyscript-pwa/)
also explains how to use the gallery bundle as a starting point for your own app.

For a desktop clone:

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay
python3 -m venv .venv
.venv/bin/pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ -r requirements.txt
cd src
../.venv/bin/python examples/pydisplay_demo.py
```

On Windows, use the equivalent `.venv\Scripts\python.exe` commands.

For MicroPython, install unprefixed MIP package names from the PyDevices
micropython-lib index, then install a board package:

```python
import mip

INDEX = "https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mip.install("displaydev", index=INDEX)
mip.install("eventsys", index=INDEX)  # optional; used by these non-LVGL examples
```

See the
[micropython-hardware install workflows](https://pydevices.github.io/micropython-hardware/install-workflows.html)
and [board configs](https://pydevices.github.io/micropython-hardware/board-configs.html)
for complete device setup.

## Runtime ownership

Board configs describe hardware. They export neutral pieces such as
`display_drv`, `touch_read`, `host_read`, and `timer_async`; they do not create
an application runtime.

Non-LVGL examples in this repo opt into the optional `eventsys` coordinator:

```python
from board_config import display_drv
from app_runtime import runtime

runtime.run_forever()
```

LVGL examples use the coordinator bundled with the LVGL binding and do not
import `eventsys`:

```python
from board_config import display_drv
from display_driver import runtime

runtime.run_forever()
```

This separation keeps hardware policy out of board configs and lets applications
provide a different event loop or traffic controller when appropriate.

## Package names

Python distributions on TestPyPI use the organization prefix; imports and MIP
packages remain conventional and unprefixed.

| TestPyPI distribution | Python import / MIP name |
|---|---|
| `pydevices-displaydev` | `displaydev` |
| `pydevices-audiodev` | `audiodev` |
| `pydevices-events` | `events` |
| `pydevices-keys` | `keys` |
| `pydevices-multimer` | `multimer` |
| `pydevices-eventsys` | `eventsys` |
| `pydevices-pygraphics` | `pygraphics` |
| `pydevices-palettes` | `palettes` |
| `pydevices-pdwidgets` | `pdwidgets` |
| `pydevices-lvgl` | `lvgl` |

## Repository layout

| Path | Purpose |
|---|---|
| `src/examples/` | Portable examples and complete demo applications |
| `src/utils/` | Example helpers and third-party GUI adapters |
| `web/pyscript/` | PyScript gallery and reusable PWA shell |
| `docs/` | Integration, platform, example, and PWA documentation |
| `tools/` | Cross-runtime example and LVGL test harnesses |
| `packages/` | GitHub MIP manifests for examples and helpers |

## Related repositories

- [micropython-hardware](https://github.com/PyDevices/micropython-hardware) — canonical product source and publishing owner
- [micropython-lib](https://github.com/PyDevices/micropython-lib) — PyDevices MIP index fork
- [lvgl-bindings](https://github.com/PyDevices/lvgl-bindings) — shared LVGL binding and `display_driver` source
- [lvgl-micropython](https://github.com/PyDevices/lvgl-micropython),
  [lvgl-circuitpython](https://github.com/PyDevices/lvgl-circuitpython), and
  [lvgl-python](https://github.com/PyDevices/lvgl-python) — runtime-specific LVGL distributions
- [pygraphics](https://github.com/PyDevices/pygraphics),
  [palettes](https://github.com/PyDevices/palettes), and
  [pdwidgets](https://github.com/PyDevices/pdwidgets) — companion packages
- [pydisplay_android](https://github.com/PyDevices/pydisplay_android) — Android application packaging

## Development

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m pytest -s tests -q
.venv/bin/ruff check src tests tools scripts
```

See [AGENTS.md](AGENTS.md) and [tools/README.md](tools/README.md) for the
cross-runtime example matrix. Contributions to reusable libraries and hardware
support belong in micropython-hardware; examples, integrations, and gallery work
belong here.

## License

MIT. See [LICENSE](LICENSE).
