# Utils

Portable helpers shared by board configs and [pydevices-examples](https://github.com/PyDevices/pydevices-examples).
Install onto `utils/` (or `.` if that directory is already on `sys.path`):

```python
import mip
mip.install("github:PyDevices/pydevices/packages/utils.json", target="./utils")
```

| Module | Role |
|--------|------|
| `byteswap.py` | Fast 16-bit pixel swap (numpy/ulab, else `viper_tools`) for `displaydev` |
| `viper_tools.py` | `@micropython.viper` bodies (`byteswap`, displaybuf bounce, tft glyph pack) |
| `mip.py` | Portable `mip` for CPython / CircuitPython / Pyodide (firmware `mip` wins on MicroPython) |
| `micropython.py` | CPython shim (`const` / `viper` / `native`) so MCU modules load |
| `keypins.py` | Key codes as pin-like objects (needs `events` + `keys` on the path) |
| `wifi.py` | MicroPython `network.WLAN` shim with a CircuitPython-shaped `wifi.radio` |
| `frame_recorder.py` | `FFmpegFrameRecorder` for desktop `PGDisplay` / `SDLDisplay` video |
