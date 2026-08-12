# micropython-lib MIP

Precompiled `.mpy` packages from the [PyDevices micropython-lib](https://github.com/PyDevices/micropython-lib) fork, served via a static MIP index.

## Package index URL

```
https://PyDevices.github.io/micropython-lib/mip/PyDevices
```

## Install a package

```python
import mip
mip.install("displaydev", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

On **PyScript MicroPython** (`micropython.html`, `mp.html`), `?deps=` installs
use the **bytecode** channel via ``utils/ps_loader.py`` (firmware ``mip`` on
MicroPython). Pyodide uses portable ``mip.py`` from pydevices
``utils/`` for manifests and modules.

With `mpremote`:

```bash
mpremote mip install --index "https://PyDevices.github.io/micropython-lib/mip/PyDevices" displaydev
```

## Available packages

**Core:**

- `displaydev`, `audiodev`, `events`, `keys`, optional `eventsys`, `multimer`,
  `pygraphics`, `palettes`, and `pdwidgets`

**Drivers** (examples):

- Display: `gc9a01`, `ili9341`, `st7789`, …
- Touch: `ft6x36`, `xpt2046`, `cst226`, …

Package names **never contain `/`**. Paths with `/` are GitHub repo installs — see [GitHub MIP](mip-github.md).

## Not available from micropython-lib

These must come from GitHub:

- `utils`, `examples`
- `spibus`, `i80bus` (viper not supported in micropython-lib packaging)
- Board config packages (use GitHub `board_configs/.../package.json`)

For combined board + package setup, use [pydevices install workflows](https://pydevices.github.io/pydevices/install-workflows.html).

## Verify install

```python
import mip
mip.install("displaydev", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
import displaydev
print(displaydev)
```

If the index is unreachable, use a [full clone](full-clone.md) or install individual
source files via GitHub paths (see [GitHub MIP](mip-github.md)). Core libraries are
not published as `packages/*.json` fallbacks.
