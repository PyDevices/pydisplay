# ⚠️ Troubleshooting

Common problems when installing, importing, or running pydisplay.

## Import errors

### `ModuleNotFoundError: No module named 'displaydev'`

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

## WSL / WSLg

### Matrix: Windows PE windows missing, or `.exe` cells report `hang`

**Symptom:** During `tools/example_test_kit.py` under
`SDL_VIDEODRIVER=dummy`, Unix runtimes stay headless (expected), but
`micropython.exe` / `python.exe` never show a window — or those cells report
`hang` while a Windows window is still up and interactive.

**Cause (missing window):** the harness forwarded `SDL_*=dummy` into PE via
wrapper `--env` / `env_set`. PE does not see WSL-exported env; only explicit
forwarding makes it headless. The kit must **not** forward `SDL_*` to `*.exe`.

**Cause (`hang` with a live window):** the example did not quit after
`duration_s` (deadline hook / inject / `Runtime.poll` path). The kit then hits
`timeout_s` and labels the cell `hang`. The process was usable the whole time —
not a failed PE launch. Pipe capture used to hide PE stdout after the timeout
kill; the kit now captures PE output to temp files.

**Fix:** restore real Windows video for PE (no `SDL_*` forward); fix the quit
path so the example exits and prints `EXAMPLE_RESULT`. Details:
[tools/README.md — Windows PE under WSL](../tools/README.md#windows-pe-under-wsl).

### Square/box artifact and touch-drag lag on long presses (touchscreen, Ubuntu/WSLg)

**Symptom:** On a touchscreen, a long press shows a small square/box popup around
the touch point, and dragging (e.g. a glissando across piano keys) feels laggy —
motion updates arrive in bursts rather than smoothly. **Mouse clicks/drags never
show the square and are not laggy.** This reproduces identically in `micropython`,
`micropython.exe`'s Linux counterpart under WSL, CircuitPython, and CPython
`.venv`, regardless of display backend (`SDLDisplay` or `PGDisplay`/PyGame).

**Cause:** This is **not a pydisplay bug**. It is WSLg's touch remoting: WSLg
forwards touch input from the Windows host to the Linux guest over the RDP
Input Extension Protocol ([MS-RDPEI](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpei/)),
which negotiates `CS_READY_FLAGS_SHOW_TOUCH_VISUALS` and applies Windows'
legacy "press and hold to right-click" gesture disambiguation — the square is
that gesture's touch-visual feedback, and the hold-to-disambiguate delay is
what shows up as drag lag. This happens **before** the event ever reaches X11
or the app.

**Confirmed environmental, not app-level**, by reproducing the identical square
+ right-click-menu behavior in `mousepad` (GTK text editor, unrelated to
pydisplay) under the same WSLg session. Disabling Windows' *Settings → Bluetooth
& devices → Touch → "Press and hold for right-click"* did **not** remove it,
which is consistent with the gesture being applied at the RDP/WSLg layer, not
by the Windows touch-input stack the setting controls.

**Fix:** None available from application code — pydisplay's SDL2/PyGame event
handling already treats touch and mouse input identically; there is no
touch-visual or gesture-disambiguation logic to disable on the app side. Native
Windows apps (`micropython.exe`, `python.exe`) are unaffected because they
receive touch input directly from the Windows touch stack, bypassing WSLg's RDP
remoting entirely. Native (non-WSL) Linux is also unaffected. Treat touch input
under WSLg as inherently laggier/gesture-delayed than mouse input or native
touch, and prefer mouse or native Windows/Linux for latency-sensitive touch
testing.

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
