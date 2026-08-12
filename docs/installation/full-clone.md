# Full clone

A pydisplay clone contains examples, application helpers, documentation, and the
PyScript/PWA site. Reusable product libraries are installed packages or come
from a sibling `micropython-hardware` checkout.

## Download

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay
```

## Layout

```text
pydisplay/
├── src/examples/       # portable demos and applications
├── src/utils/          # example and GUI integration helpers
├── web/pyscript/       # live gallery and reusable PWA shell
├── packages/           # GitHub MIP manifests for examples/helpers
└── tools/              # cross-runtime test harnesses
```

For a complete editable workspace:

```bash
git clone https://github.com/PyDevices/micropython-hardware.git
git clone https://github.com/PyDevices/pydisplay.git
```

Keep the two repositories as siblings. `src/utils/path.py` recognizes that
layout and adds the product `lib`, `utils`, display, and audio source trees.

## Run on desktop

The simplest route installs the TestPyPI products into a virtual environment:

```bash
cd pydisplay
python3 -m venv .venv
.venv/bin/pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ -r requirements.txt
cd src
../.venv/bin/python examples/pydisplay_demo.py
```

See [Desktop CPython](../guides/desktop-cpython.md) for system dependencies and
editable source paths.

## Run on a microcontroller

Install product and board packages using the
[micropython-hardware workflows](https://pydevices.github.io/micropython-hardware/install-workflows.html),
then install pydisplay's `examples.json` and `utils.json` when desired. See the
[ESP32 guide](../guides/esp32-board.md).

## Regenerate gallery manifests

When example or utility files change, maintainers run:

```bash
./scripts/install_refresh_manifests.sh
python scripts/gallery_generator.py
```

Product publishing and MIP synchronization are owned by micropython-hardware.
