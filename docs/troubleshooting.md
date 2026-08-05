# ⚠️ Troubleshooting

Common problems when installing, importing, or running pydisplay.

## Import errors

### `ModuleNotFoundError: No module named 'displaysys'`

**Cause:** Packages are not on `sys.path`.

**Fix:**

- **Full clone:** `cd src` and set `PYTHONPATH`/`MICROPYPATH` to `.:lib:utils` before running (preferred), or `import utils.path` if `utils/` is present and environment variables are unavailable or not set as recommended (see [Utils path setup](utils.md#path-setup)).
- **Device:** install via [MIP](installation/mip-github.md) or [micropython-hardware install workflows](https://pydevices.github.io/micropython-hardware/install-workflows.html) into `/lib`.
- **Examples under `mpremote mount .`:** `import utils.path` (see [Utils path setup](utils.md#path-setup)), then resolve demos as a package — `from examples import hello`, not a bare `import hello` (the mounted tree still nests `examples/`).

### `ModuleNotFoundError: No module named 'board_config'`

**Cause:** No `board_config.py` for your hardware.

**Fix:** Install a [board config package](https://pydevices.github.io/micropython-hardware/board-configs.html) or copy one into `lib/`:

```python
import mip
mip.install("github:PyDevices/micropython-hardware/board_configs/sdldisplay")  # desktop SDL2
```

### `ImportError: multimer is required for auto_refresh`

**Cause:** Display was created with `auto_refresh=True` but `multimer` is not installed.

**Fix:** Install `multimer` or set `auto_refresh=False`.

## MIP / install failures

### `mip` network or SSL errors on device

**Fix:** Use `mpremote mip install` from your PC, or copy files with `mpremote cp`. Check Wi-Fi on the board for OTA installs.

### Wrong or outdated packages after editing the repo

**Fix (maintainers):** run `./scripts/install_refresh_manifests.sh` and reinstall. Users should reinstall the board config and core packages after upstream updates.

## Display issues

### Blank window on desktop (CPython)

**Fix:**

1. Confirm SDL2 dev libraries are installed — see [Desktop CPython](guides/desktop-cpython.md).
2. Try **PGDisplay** (PyGame) instead of SDL2.
3. Run `python3 examples/hello.py` from `src/` (with `PYTHONPATH=.:lib:utils`) — a window should appear immediately.

### Wrong colors or garbled pixels on MCU

**Fix:**

1. Verify the correct [board config](https://pydevices.github.io/micropython-hardware/board-configs.html) for your wiring.
2. Check `requires_byteswap` / `BusDisplay.disable_auto_byteswap()` — see [display drivers](https://pydevices.github.io/micropython-hardware/display-drivers.html).
3. Confirm SPI/I80 pins match your schematic.

### Touch coordinates wrong or inverted

**Fix:** Touch driver and rotation must match the display. Set `display.rotation` and ensure the touch device has a matching `rotation` attribute.

## PyScript / browser

### Tab hangs or freezes

**Cause:** Blocking `while True:` loop without `await`.

**Fix:** Port to asyncio — see [PyScript asyncio guide](guides/pyscript-asyncio.md).

### Example not listed in demo hub

**Cause:** Only asyncio-compatible examples run in the browser.

**Fix:** Start with `calc_graphics.py`, `paint.py`, or `eventsys_simpletest.py`.

## Wokwi

### Simulation starts but display stays blank

**Fix:** Use files from [`wokwi/`](../../web/wokwi/). Confirm `main.py` installs the core packages and the Wokwi board config before `import testris`.

### `IndexError` on last keypad row (`TouchKeypad`)

Known Wokwi simulator quirk with `eventsys.touch_keypad.TouchKeypad` — may not reproduce on real hardware.

## Documentation / API reference

### Griffe warnings during `mkdocs build`

Docstring parameter names do not match the function signature (often `*args` wrappers). The site still builds; fix docstrings or signatures in source when you touch that module.

## 💬 Still stuck?

See [Getting help](getting-help.md) for issue reporting guidelines.

Include: board/OS, MicroPython or CPython version, board config path, and a minimal reproduction script.
