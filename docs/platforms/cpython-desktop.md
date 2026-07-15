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

On Windows and macOS, default **`multimer.Timer`** uses **`_win32`** (APC) when available, otherwise a background thread. When CPython falls back to the **`multimer._sdl2`** backend, it imports timer APIs from **`usdl2`** first when available, then ctypes against system libSDL2. See [multimer](../concepts/multimer.md).

## PGDisplay fallback

PyGame CE (`pygame-ce` on PyPI; `import pygame`) is easier to install and avoids some SDL2 issues (especially on Windows and Chromebooks):

```bash
pip install pygame-ce
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

Mouse events map to touch events. Keyboard and encoder devices work on desktop the same as on embedded targets.

## Linux KMS (no window manager)

For embedded Linux **without** X11/Wayland (Pi console, kiosk, headless HDMI), use SDL’s **kmsdrm** video driver with the existing `SDLDisplay` + `usdl2` stack — not a native `/dev/fb0` path.

**Board config:** `board_configs/sdldisplay/linux_kms/` sets `SDL_VIDEODRIVER=kmsdrm` before `SDLDisplay` initializes and opens a fullscreen window.

```bash
# Install the KMS config (clone or MIP), then run as usual from src/
cp ../board_configs/sdldisplay/linux_kms/board_config.py lib/board_config.py
# or: mip.install("github:PyDevices/pydisplay/board_configs/sdldisplay/linux_kms")
cd pydisplay/src
python3 -i path.py
```

**Prerequisites**

- `libsdl2` built with the **kmsdrm** backend (stock Debian/Raspberry Pi OS packages usually are)
- Access to `/dev/dri/*` (user in `video` / `render` group, or root)
- A free VT / no competing DRM master (stop the desktop session first)
- Input via SDL (evdev keyboards, mice, gamepads)

**Contrast**

| Path | Env / config | Use when |
|------|----------------|----------|
| Desktop Linux (this page above) | default SDL (x11/wayland) | Normal desktop session |
| **KMS** | `SDL_VIDEODRIVER=kmsdrm` + `sdldisplay/linux_kms` | No WM; direct scanout |
| Headless CI | `SDL_VIDEODRIVER=dummy` | No display hardware |

Native Linux fbdev/DRM modules are **out of scope** until this SDL KMS path is insufficient.

## Single-board computers

CircuitPython with Blinka on Raspberry Pi and similar boards is planned but not fully tested. For **CPython + HDMI without a desktop**, prefer [Linux KMS](#linux-kms-no-window-manager) above. Track other SBC work on the [roadmap](https://github.com/PyDevices/pydisplay#roadmap).
