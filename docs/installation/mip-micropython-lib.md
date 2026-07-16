# micropython-lib MIP

Precompiled `.mpy` packages from the [PyDevices micropython-lib](https://github.com/PyDevices/micropython-lib) fork, served via a static MIP index.

## Package index URL

```
https://PyDevices.github.io/micropython-lib/mip/PyDevices
```

## Install a package

```python
import mip
mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

On **PyScript MicroPython** (`micropython.html`, `run.html`), `?deps=` / `?mip=` installs
use the **bytecode** channel via ``add_ons/ps_loader.py`` (firmware ``mip`` on
MicroPython; portable ``mip.py`` on Pyodide for manifests/modules).

With `mpremote`:

```bash
mpremote mip install --index "https://PyDevices.github.io/micropython-lib/mip/PyDevices" displaysys
```

## Available packages

**Core:**

- `displaysys`, `eventsys`, `graphics`, `multimer`

**Display extensions** (pull in `displaysys` automatically):

- `displaysys-busdisplay`, `displaysys-epaperdisplay`, `displaysys-fbdisplay`, `displaysys-jndisplay`, `displaysys-pgdisplay`, `displaysys-pixeldisplay`, `displaysys-psdisplay`, `displaysys-sdldisplay`

**Drivers** (examples):

- Display: `gc9a01`, `ili9341`, `st7789`, …
- Touch: `ft6x36`, `xpt2046`, `cst226`, …

Package names **never contain `/`**. Paths with `/` are GitHub repo installs — see [GitHub MIP](mip-github.md).

## Not available from micropython-lib

These must come from GitHub:

- `add_ons`, `examples`
- `spibus`, `i80bus` (viper not supported in micropython-lib packaging)
- Board config packages (use GitHub `board_configs/.../package.json`)

The [installer.py](installer.md) script installs micropython-lib packages plus GitHub add_ons, examples, and `board_config.py` in one step.

## Verify install

```python
import mip
mip.install("displaysys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
import displaysys
print(displaysys)
```

If the index is unreachable, fall back to [GitHub MIP](mip-github.md) source packages.
