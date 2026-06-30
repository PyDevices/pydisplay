# Troubleshooting

Common problems when installing, importing, or running pydisplay.

## Import errors

### `ModuleNotFoundError: No module named 'displaysys'`

**Cause:** Packages are not on `sys.path`.

**Fix:**

- **Full clone:** run from `src/` and `import path` first, or `python3 -i path.py`.
- **Device:** install via [MIP](installation/mip-github.md) or [installer.py](installation/installer.md) into `/lib`.
- **Examples:** `import lib.path` before `import hello` when using `mpremote mount`.

### `ModuleNotFoundError: No module named 'board_config'`

**Cause:** No `board_config.py` for your hardware.

**Fix:** Install a [board config package](hardware/board-configs.md) or copy one into `lib/`:

```python
import mip
mip.install("github:PyDevices/pydisplay/board_configs/sdldisplay")  # desktop SDL2
```

### `ImportError: multimer is required for auto_refresh`

**Cause:** Display was created with `auto_refresh=True` but `multimer` is not installed.

**Fix:** Install `multimer` or set `auto_refresh=False`.

## MIP / install failures

### `mip` network or SSL errors on device

**Fix:** Use `mpremote mip install` from your PC, or copy files with `mpremote cp`. Check Wi-Fi on the board for OTA installs.

### Wrong or outdated packages after editing the repo

**Fix (maintainers):** run `./scripts/install_refresh_manifests.sh` and reinstall. Users should reinstall the board config and bundle packages after upstream updates.

## Display issues

### Blank window on desktop (CPython)

**Fix:**

1. Confirm SDL2 dev libraries are installed — see [Desktop CPython](guides/desktop-cpython.md).
2. Try **PGDisplay** (PyGame) instead of SDL2.
3. Run `import hello` after `path.py` — a window should appear immediately.

### Wrong colors or garbled pixels on MCU

**Fix:**

1. Verify the correct [board config](hardware/board-configs.md) for your wiring.
2. Check `requires_byteswap` / `BusDisplay.disable_auto_byteswap()` — see [display drivers](hardware/display-drivers.md).
3. Confirm SPI/I80 pins match your schematic.

### Touch coordinates wrong or inverted

**Fix:** Touch driver and rotation must match the display. Set `display.rotation` and ensure the touch device has a matching `rotation` attribute.

## PyScript / browser

### Tab hangs or freezes

**Cause:** Blocking `while True:` loop without `await`.

**Fix:** Port to asyncio — see [PyScript asyncio guide](guides/pyscript-asyncio.md).

### Example not listed in demo hub

**Cause:** Only asyncio-compatible examples run in the browser.

**Fix:** Start with `calculator.py`, `paint.py`, or `eventsys_simpletest.py`.

## Wokwi

### Simulation starts but display stays blank

**Fix:** Use files from [`wokwi/`](../sim/wokwi/). Confirm `main.py` installs the pydisplay bundle and Wokwi board config before `import testris`.

### `IndexError` on last keypad row (touch_keypad example)

Known Wokwi simulator quirk — may not reproduce on real hardware.

## Documentation / API reference

### Griffe warnings during `mkdocs build`

Docstring parameter names do not match the function signature (often `*args` wrappers). The site still builds; fix docstrings or signatures in source when you touch that module.

## Still stuck?

See [Getting help](getting-help.md) for issue reporting guidelines.

Include: board/OS, MicroPython or CPython version, board config path, and a minimal reproduction script.
