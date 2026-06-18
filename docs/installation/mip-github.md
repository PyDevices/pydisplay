# GitHub MIP packages

Install source `.py` files directly from the pydisplay GitHub repository using MicroPython's `mip` module.

## Bundle install (recommended)

Installs core libraries and default `board_config.py` (not examples or add_ons):

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/pydisplay-bundle.json", target=".")
```

With `mpremote`:

```bash
mpremote mip install --target "." "github:PyDevices/pydisplay/packages/pydisplay-bundle.json"
```

Add examples and add_ons separately:

```python
mip.install("github:PyDevices/pydisplay/packages/examples.json", target=".")
mip.install("github:PyDevices/pydisplay/packages/add_ons.json", target="./add_ons")
```

## Individual packages

Manifests live in the [`packages/`](https://github.com/PyDevices/pydisplay/tree/main/packages) directory:

| Package | Manifest |
|---------|----------|
| displaysys | `packages/displaysys.json` |
| eventsys | `packages/eventsys.json` |
| graphics | `packages/graphics.json` |
| palettes | `packages/palettes.json` |
| multimer | `packages/multimer.json` |
| add_ons | `packages/add_ons.json` |
| examples | `packages/examples.json` |
| spibus | `packages/spibus.json` |
| i80bus | `packages/i80bus.json` |

Example:

```python
mip.install("github:PyDevices/pydisplay/packages/displaysys.json")
```

## Board configs

Each board directory includes a `package.json` that installs `board_config.py`, required drivers, and bus drivers:

```python
mip.install("github:PyDevices/pydisplay/board_configs/busdisplay/i80/wt32sc01-plus")
```

See the [board config index](../hardware/board-configs.md) for all paths.

## Single files

`mip` can fetch any file from the repo by URL path:

```python
mip.install("github:PyDevices/pydisplay/src/lib/path.py", target=".")
mip.install("github:PyDevices/pydisplay/drivers/display/st7789.py", target="./drivers/display")
```

## Notes

- Packages use **source** `.py` files (not `.mpy` bytecode).
- `spibus` and `i80bus` use `@micropython.viper` and are only available via GitHub, not micropython-lib.
- After install, import `path.py` unless everything lives under `lib/` on the path.
