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
├── lib/                 # core packages (displaysys, eventsys, events.py, keys.py, …)
├── examples/            # demo scripts
├── utils/               # optional extensions — path.py, color_setup, tft_config, gui/, …
```

Optional third-party add-ons (not in git): copy [Nano-GUI](../guis/nano-gui.md) `gui/` into `utils/gui/`.

## Run on desktop

Preferred: set `PYTHONPATH=.:lib:utils` (MicroPython: `MICROPYPATH` instead), `cd src`, and run the interpreter directly on a file — no path bootstrap needed. See [Desktop CPython quick start](../guides/desktop-cpython.md) for dependencies and first run.

## Run on a microcontroller

See [ESP32 board quick start](../guides/esp32-board.md) for MIP install and `mpremote` workflow.

## utils/path.py

`utils/path.py` prepends `lib/`, `utils/`, and cwd to `sys.path` so imports like `import displaysys` work without installing into `/lib` on the device. It never adds `examples/` — example scripts are always reached as `from examples import <name>` / `import examples.<name>`, not by putting `examples/` on `sys.path`.

On desktop, prefer setting `PYTHONPATH`/`MICROPYPATH` (see above) so you never need to import it. `utils/path.py` is for targets where environment variables are unavailable or not set as recommended: a bare device REPL, or a `boot.py`/`main.py` entry point, when `utils/` is present on the device. Omit `utils/` and `import utils.path` entirely if everything is installed flat into `/lib` — that's already on `sys.path`.

## Regenerating package manifests

If you edit files under `src/`, maintainers should run from the repo root:

```bash
./scripts/install_refresh_manifests.sh
```

This updates `packages/*.json` and `web/pyscript/micropython.toml`. See [tools/README.md](https://github.com/PyDevices/pydisplay/blob/main/tools/README.md).
