# ESP32 / MicroPython board

**Who:** You have a MicroPython board (ESP32-S3, WT32-SC01, etc.) and want pydisplay running on hardware.

**Prerequisites:** USB serial access, `mpremote` on your PC. No prior pydisplay install.

## 1. Pick a board config

Find your hardware in [board configs](https://pydevices.github.io/micropython-hardware/board-configs.html). Example for WT32-SC01 Plus:

```
board_configs/busdisplay/i80/wt32sc01-plus
```

Don't see your board? Use the closest match or [contribute a config](https://pydevices.github.io/micropython-hardware/board-configs.html).

## 2. Install packages

**Option A — installer.py (recommended):**

Follow [installer.py](../installation/installer.md) on the device or via `mpremote run`.

**Option B — MIP from your PC:**

```bash
INDEX="https://PyDevices.github.io/micropython-lib/mip/PyDevices"
mpremote mip install "github:PyDevices/micropython-hardware/board_configs/busdisplay/i80/wt32sc01-plus"
for pkg in displaysys eventsys pygraphics multimer; do
  mpremote mip install --index "$INDEX" "$pkg"
done
mpremote mip install --target "./utils" "github:PyDevices/pydisplay/packages/utils.json"
```

**Option C — minimum packages only:**

--8<-- "_snippets/minimum-mip.md"

## 3. Run the demo

From the repo `src/` on your PC:

```bash
mpremote mount .
```

At the device REPL:

```python
import utils.path
from examples import pydisplay_demo
```

Under a mounted dev tree, `examples/` stays a subdirectory — resolve it as a package (`from examples import <name>` / `import examples.<a>.<b>`), never a bare `import <name>`. If instead you MIP-installed `examples.json` with `target="."` (flat, no `examples/` subdirectory), the same demo is a bare import:

```python
import pydisplay_demo
```

See [**pydisplay_demo**](../examples/pydisplay_demo.md) for what the script demonstrates (clicks, rotation, scrolling). To start your own app, copy the [**App starter**](../examples/app-starter.md) boilerplate. Legacy `hello.py` uses `tft_config` if you are porting older st7789py examples.

## 4. Try events

```python
import utils.path
from examples import eventsys_simpletest
```

## Background network / workers

ESP32 MicroPython `_thread` stacks are tiny. Prefer a job queue drained from
`runtime.on_tick` (or an LVGL timer) over `start_new_thread` for HTTP and
discovery. Details: [MicroPython platform notes](../platforms/micropython.md#background-work-_thread).

## Next

- [**App starter**](../examples/app-starter.md) — copy-paste template for your first app
- [**pydisplay_demo**](../examples/pydisplay_demo.md) — flagship feature demo (display, input, scroll)
- [Examples catalog](../examples/index.md) — suggested learning order
- [Events concept](../concepts/events.md) — runtime poll loop
- [MicroPython platform notes](../platforms/micropython.md) — bus drivers, frozen firmware
- [Troubleshooting](../troubleshooting.md)

## Reference

- [API reference (core)](../reference/) → `displaysys`, `eventsys`
