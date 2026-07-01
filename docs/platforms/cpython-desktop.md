# CPython desktop

Platform-specific notes for SDL2, PyGame, and OS dependencies. **First run:** use the [Desktop CPython quick start](../guides/desktop-cpython.md).

## Dependencies

Install SDL2 development libraries (Linux/macOS) or PyGame (Windows fallback). The [desktop quick start](../guides/desktop-cpython.md) links here for OS-specific packages.

## Linux (including WSL)

Install SDL2 development libraries, then run as above.

**Debian / Ubuntu / WSL:**

```bash
sudo apt update
sudo apt install libsdl2-dev python3-venv
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
python3 -i path.py
```

**Fedora:**

```bash
sudo dnf install SDL2-devel
```

If SDL2 fails or is unavailable, use PyGame instead — see [PGDisplay fallback](#pgdisplay-fallback) below.

## macOS

```bash
brew install sdl2
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
python3 -i path.py
```

## Windows

SDL2 native libraries can be awkward on Windows. Recommended path:

1. Install [Python 3](https://www.python.org/downloads/) (check "Add to PATH").
2. Use **PGDisplay** (PyGame) instead of SDL2 — see below.
3. Or develop in **WSL** with the Linux instructions above.

On Windows and macOS, default **`multimer.Timer`** uses **`_win32`** (APC, no pump) when available, otherwise a background thread. Call **`pump()`** only when **`needs_pump()`** is true (thread/SDL/polling backends). When CPython falls back to the **`multimer._sdl2`** backend, it imports timer APIs from **`usdl2`** first when available, then ctypes against system libSDL2.

## PGDisplay fallback

PyGame is easier to install and avoids some SDL2 issues (especially on Windows and Chromebooks):

```bash
pip install pygame
```

Use the PyGame board config. From a clone, copy or symlink before running:

```bash
cp ../board_configs/pgdisplay/board_config.py lib/board_config.py
cd pydisplay/src
python3 -i path.py
```

Or install via MIP on MicroPython Unix:

```python
mip.install("github:PyDevices/pydisplay/board_configs/pgdisplay")
```

| Config path | Display class |
|-------------|---------------|
| `board_configs/sdldisplay/` | `SDLDisplay` (SDL2) |
| `board_configs/pgdisplay/` | `PGDisplay` (PyGame) |

The default `src/lib/board_config.py` selects `PGDisplay` on CPython when PyGame is installed, otherwise `SDLDisplay`.

## MicroPython on Unix

Same layout as CPython, but use the MicroPython interpreter:

```bash
micropython -i path.py
```

Install SDL2/PyGame for your OS first; MicroPython Unix builds vary in bundled modules.

## Input

Mouse events map to touch events. Keyboard and encoder brokers work on desktop the same as on embedded targets.

## Single-board computers

CircuitPython with Blinka on Raspberry Pi and similar boards is planned but not fully tested. Track progress on the [roadmap](https://github.com/PyDevices/pydisplay#roadmap).
