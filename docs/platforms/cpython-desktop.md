# CPython desktop

Develop and debug on Linux, macOS, or Windows using SDL2 or PyGame backends.

## Dependencies

**SDL2Display (preferred)** — faster; uses SDL2:

- Linux: install `libsdl2-dev` (or your distro equivalent)
- macOS: `brew install sdl2`
- Windows: install SDL2 development libraries or use PyGame fallback

**PGDisplay (optional)** — uses PyGame:

```bash
pip install pygame
```

PGDisplay is useful when SDL2 glitches (some Chromebooks) or when SDL2 is hard to install on Windows.

## Run from a clone

```bash
cd pydisplay/src
python3 -i path.py
```

```python
>>> import hello
>>> import calculator
```

Default desktop config: `src/lib/board_config.py` (SDL2). For PyGame explicitly, use `board_configs/pgdisplay/board_config.py`.

## board_config.py

Copy or symlink the config you need:

| Config path | Display class |
|-------------|---------------|
| `board_configs/sdldisplay/` | SDL2Display |
| `board_configs/pgdisplay/` | PGDisplay |

Install via MIP on MicroPython Unix:

```python
mip.install("github:PyDevices/pydisplay/board_configs/sdldisplay")
```

## Input

Mouse events map to touch events. Keyboard and encoder brokers work on desktop the same as on embedded targets.

## Single-board computers

CircuitPython with Blinka on Raspberry Pi and similar boards is planned but not fully tested. Track progress on the [roadmap](https://github.com/PyDevices/pydisplay#roadmap).
