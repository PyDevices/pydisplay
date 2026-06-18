# CPython desktop

Develop and debug on Linux, macOS, or Windows using SDL2 or PyGame backends.

## Quick start (after dependencies)

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
python3 -i path.py
```

```python
>>> import hello
```

Default config: `src/lib/board_config.py` (SDL2Display). A window should open with the hello example.

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
| `board_configs/sdldisplay/` | SDL2Display (default `src/lib/board_config.py`) |
| `board_configs/pgdisplay/` | PGDisplay |

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
