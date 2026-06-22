# Full clone

Best for development, running all examples, and desktop testing with CPython or MicroPython on Unix.

## Download

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
```

Or download the [zip archive](https://github.com/PyDevices/pydisplay/archive/refs/heads/main.zip) and extract it.

## Layout

The `src/` directory mirrors what a device filesystem looks like after installing packages:

```
src/
├── path.py              # adds lib/, examples/, add_ons/ to sys.path
├── lib/                 # core packages (displaysys, eventsys, …)
├── examples/            # demo scripts
├── add_ons/             # optional extensions (color_setup, tft_config, gui/, …)
```

Optional third-party add-ons (not in git): copy [Nano-GUI](../guis/nano-gui.md) `gui/` into `add_ons/gui/`.

## Run on desktop

See [Desktop CPython quick start](../guides/desktop-cpython.md) for dependencies and first run.

## Run on a microcontroller

See [ESP32 board quick start](../guides/esp32-board.md) for MIP install and `mpremote` workflow.

## path.py

`path.py` prepends `lib/`, `examples/`, and `add_ons/` to `sys.path` so imports like `import displaysys` and `import hello` work without installing into `lib/` on the device.

For production firmware you may freeze modules or install into `/lib` and omit `path.py`.

## Regenerating package manifests

If you edit files under `src/`, maintainers should run from the repo root:

```bash
./tools/regenerate.sh
```

This updates `packages/*.json` and `html/pyscript.toml`. See [tools/README.md](https://github.com/PyDevices/pydisplay/blob/main/tools/README.md).
