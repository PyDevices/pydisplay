# ESP32 / MicroPython board

**Who:** You have a MicroPython board (ESP32-S3, WT32-SC01, etc.) and want pydisplay running on hardware.

**Prerequisites:** USB serial access, `mpremote` on your PC. No prior pydisplay install.

## 1. Pick a board config

Find your hardware in [board configs](../hardware/board-configs.md). Example for WT32-SC01 Plus:

```
board_configs/busdisplay/i80/wt32sc01-plus
```

Don't see your board? Use the closest match or [contribute a config](../hardware/board-configs.md).

## 2. Install packages

**Option A — installer.py (recommended):**

Follow [installer.py](../installation/installer.md) on the device or via `mpremote run`.

**Option B — MIP from your PC:**

```bash
mpremote mip install "github:PyDevices/pydisplay/board_configs/busdisplay/i80/wt32sc01-plus"
mpremote mip install "github:PyDevices/pydisplay/packages/pydisplay-bundle.json"
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
import lib.path
import pydisplay_demo
```

If packages are installed into `/lib` on the device (no mount), skip `lib.path`:

```python
import pydisplay_demo
```

See [**pydisplay_demo**](../examples/pydisplay_demo.md) for what the script demonstrates (clicks, rotation, scrolling). To start your own app, copy the [**App starter**](../examples/app-starter.md) boilerplate. Legacy `hello.py` uses `tft_config` if you are porting older st7789py examples.

## 4. Try events

```python
import lib.path
import eventsys_simpletest
```

## Next

- [**App starter**](../examples/app-starter.md) — copy-paste template for your first app
- [**pydisplay_demo**](../examples/pydisplay_demo.md) — flagship feature demo (display, input, scroll)
- [Examples catalog](../examples/index.md) — suggested learning order
- [Events concept](../concepts/events.md) — broker poll loop
- [MicroPython platform notes](../platforms/micropython.md) — bus drivers, frozen firmware
- [Troubleshooting](../troubleshooting.md)

## Reference

- [API reference (core)](../reference/) → `displaysys`, `eventsys`
