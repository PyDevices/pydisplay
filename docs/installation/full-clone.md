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
├── add_ons/             # optional extensions (color_setup, tft_config, …)
```

## Run on desktop

Install display dependencies for your platform (see [CPython desktop](../platforms/cpython-desktop.md)), then:

```bash
cd src
python3 -i path.py
```

```python
>>> import hello
```

Use `micropython -i path.py` instead of `python3` to test with MicroPython on Unix.

## Run on a microcontroller

1. Copy or MIP-install the packages you need (see [GitHub MIP](mip-github.md)).
2. Install a [board config](../hardware/board-configs.md).
3. Use `mpremote mount .` from `src/` or copy files to the device.

## path.py

`path.py` prepends `lib/`, `examples/`, and `add_ons/` to `sys.path` so imports like `import displaysys` and `import hello` work without installing into `lib/` on the device.

For production firmware you may freeze modules or install into `/lib` and omit `path.py`.

## Regenerating package manifests

If you edit files under `src/`, maintainers should run from the repo root:

```bash
./tools/regenerate.sh
```

This updates `packages/*.json` and `html/pyscript.toml`. See [tools/README.md](https://github.com/PyDevices/pydisplay/blob/main/tools/README.md).
