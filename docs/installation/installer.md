# installer.py

Universal MicroPython installer that pulls from both the micropython-lib index and the pydisplay GitHub repo.

## Download installer.py

**Browser:** [github.com/PyDevices/pydisplay/blob/main/installer.py](https://github.com/PyDevices/pydisplay/blob/main/installer.py)

**On device:**

```python
import mip
mip.install("github:PyDevices/pydisplay/installer.py")
```

**On host:**

```bash
wget https://raw.githubusercontent.com/PyDevices/pydisplay/main/installer.py
```

## Usage

```python
from installer import install

install("pydisplay-bundle")                              # micropython-lib
install("/packages/add_ons.json", target="./add_ons")      # GitHub
install("/packages/examples.json", target="./examples")    # GitHub
install("/board_configs/busdisplay/i80/wt32sc01-plus")     # GitHub board package
install("/src/lib/board_config.py", target="./")           # default desktop config
install("/src/lib/path.py", target="./")
```

The default block at the bottom of `installer.py` runs a full install when you `import installer` — edit that section to match your hardware.

## How routing works

| Argument pattern | Source | Function |
|------------------|--------|----------|
| No `/` in name (e.g. `displaysys`) | micropython-lib `.mpy` | `lib_install()` |
| Contains `/` (e.g. `/packages/examples.json`) | GitHub source `.py` | `repo_install()` |

Index URL for lib packages:

```
https://PyDevices.github.io/micropython-lib/mip/PyDevices
```

## Wokwi demo

See the installer in action: uncomment the `add_ons` / `examples` lines in [`wokwi/main.py`](https://github.com/PyDevices/pydisplay/blob/main/wokwi/main.py) ([Wokwi guide](../guides/wokwi.md)).

## Custom installs

Copy lines from the comment block in `installer.py` and adjust targets. Example minimal LVGL setup:

```python
install("displaysys")
install("eventsys")
install("/board_configs/busdisplay/spi/wokwi_ili9341_ft6x36_esp32s3")
```

Then `import path` and your application module.
