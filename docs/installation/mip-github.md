# GitHub MIP packages

Install source `.py` files directly from the pydevices-examples GitHub repository using MicroPython's `mip` module.

Core libraries (`displaydev`, `eventsys`, `multimer`, `pygraphics`,
`palettes`, `pdwidgets`) are **not** published as `packages/*.json` here —
use the [micropython-lib MIP index](mip-micropython-lib.md) instead.
Desktop `usdl2` comes with the pydevices MIP desktop board package
(or `pydevices-desktop` on TestPyPI), not as a core micropython-lib package.

## What remains on GitHub MIP

```python
import mip
mip.install("github:PyDevices/pydevices-examples/packages/examples.json", target=".")
mip.install("github:PyDevices/pydevices-examples/packages/utils.json", target="./utils")
```

With `mpremote`:

```bash
mpremote mip install --target "." "github:PyDevices/pydevices-examples/packages/examples.json"
mpremote mip install --target "./utils" "github:PyDevices/pydevices-examples/packages/utils.json"
```

## Individual packages

Manifests live in the [`packages/`](https://github.com/PyDevices/pydevices-examples/tree/main/packages) directory:

| Package | Manifest |
|---------|----------|
| utils | `packages/utils.json` |
| examples | `packages/examples.json` |
| Per-demo bundles | `packages/<example>.json` (PyScript `?manifests=`) |
| Hinch GUI mirrors | `packages/micropython-{nano-gui,micro-gui,touch}.json` |

Example:

```python
mip.install("github:PyDevices/pydevices-examples/packages/utils.json", target="./utils")
```

Bus / touch / chip-helper MIP packages (`spibus`, `i80bus`, `i2cbus`,
`tt21100`, …) and portable helpers (`byteswap`, `mip`, `viper_tools`,
`keypins`, `wifi`, `frame_recorder`) live in
[`pydevices/packages/`](https://github.com/PyDevices/pydevices/tree/main/packages)
(`utils.json` is a dependency of pydevices-examples `packages/utils.json`).

## Board configs

Each board directory includes a `package.json` that installs `board_config.py`, required drivers, and bus drivers:

```python
mip.install("github:PyDevices/pydevices/board_configs/busdisplay/i80/wt32sc01-plus")
```

See the [board config index](https://pydevices.github.io/pydevices/board-configs.html) for all paths.

## Single files

`mip` can fetch any file from the repo by URL path:

```python
mip.install("github:PyDevices/pydevices-examples/src/utils/path.py", target=".")
mip.install("github:PyDevices/pydevices/drivers/display/st7789.py", target="./drivers/display")
```

## Notes

- Packages use **source** `.py` files (not `.mpy` bytecode).
- `spibus` and `i80bus` (in pydevices) use `@micropython.viper` and are only available via GitHub, not micropython-lib.
- After install, see [Utils path setup](../utils.md#path-setup) when environment variables are unavailable or not set as recommended. Skip this if everything lives flat under `/lib`.
