# Desktop utility modules

Every non-debris runtime module placed directly under this directory is
automatically included in both the pip and MIP `pydevices-desktop` packages and
in `pydevices-desktop.toml`. Utilities do not publish as separate packages.

| Module | Role |
|---|---|
| `mip.py` | Portable `mip` for CPython, CircuitPython, and Pyodide |
| `micropython.py` | CPython compatibility shim for common MicroPython decorators and helpers |
| `frame_recorder.py` | FFmpeg recording for desktop displays |
| `usdl2.py` | Pure-Python SDL2 FFI fallback |
| `uwin32.py` | Pure-Python Win32 FFI fallback |

Firmware-frozen modules resolve before `lib` in the documented preferred
`MICROPYPATH`, so bundled fallbacks do not replace native firmware modules.
