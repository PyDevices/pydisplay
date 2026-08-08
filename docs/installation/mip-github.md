# GitHub MIP packages

Install source `.py` files directly from the pydisplay GitHub repository using MicroPython's `mip` module.

Core libraries (`displaysys`, `eventsys`, `multimer`, `pygraphics`,
`palettes`, `pdwidgets`) are **not** published as `packages/*.json` here —
use the [micropython-lib MIP index](mip-micropython-lib.md) instead.
Desktop `usdl2` comes with the micropython-hardware MIP desktop board package
(or `pydisplay-desktop` on TestPyPI), not as a core micropython-lib package.

## What remains on GitHub MIP

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/examples.json", target=".")
mip.install("github:PyDevices/pydisplay/packages/utils.json", target="./utils")
```

With `mpremote`:

```bash
mpremote mip install --target "." "github:PyDevices/pydisplay/packages/examples.json"
mpremote mip install --target "./utils" "github:PyDevices/pydisplay/packages/utils.json"
```

## Individual packages

Manifests live in the [`packages/`](https://github.com/PyDevices/pydisplay/tree/main/packages) directory:

| Package | Manifest |
|---------|----------|
| utils | `packages/utils.json` |
| examples | `packages/examples.json` |
| Per-demo bundles | `packages/<example>.json` (PyScript `?manifests=`) |
| Hinch GUI mirrors | `packages/micropython-{nano-gui,micro-gui,touch}.json` |

Example:

```python
mip.install("github:PyDevices/pydisplay/packages/utils.json", target="./utils")
```

Bus / touch / chip-helper MIP packages (`spibus`, `i80bus`, `i2cbus`,
`tt21100`, …) live in
[`micropython-hardware/packages/`](https://github.com/PyDevices/micropython-hardware/tree/main/packages).

## Board configs

Each board directory includes a `package.json` that installs `board_config.py`, required drivers, and bus drivers:

```python
mip.install("github:PyDevices/micropython-hardware/board_configs/busdisplay/i80/wt32sc01-plus")
```

See the [board config index](https://pydevices.github.io/micropython-hardware/board-configs.html) for all paths.

## Single files

`mip` can fetch any file from the repo by URL path:

```python
mip.install("github:PyDevices/pydisplay/src/utils/path.py", target=".")
mip.install("github:PyDevices/micropython-hardware/drivers/display/st7789.py", target="./drivers/display")
```

## Notes

- Packages use **source** `.py` files (not `.mpy` bytecode).
- `spibus` and `i80bus` (in micropython-hardware) use `@micropython.viper` and are only available via GitHub, not micropython-lib.
- After install, see [Utils path setup](../utils.md#path-setup) when environment variables are unavailable or not set as recommended. Skip this if everything lives flat under `/lib`.
