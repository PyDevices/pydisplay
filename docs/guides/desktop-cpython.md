# Desktop CPython

**Who:** You develop on Linux, macOS, or Windows with CPython and want a local display window.

**Prerequisites:** Python 3, git. See [CPython desktop platform guide](../platforms/cpython-desktop.md) for OS-specific SDL2/PyGame setup.

## Dependencies

Install SDL2 development libraries for your OS, or use PyGame (PGDisplay) — details in [platforms/cpython-desktop.md](../platforms/cpython-desktop.md).

## First run

--8<-- "_snippets/first-run-desktop.md"

Default config uses **SDL2Display** (`src/lib/board_config.py`).

## PyGame fallback

If SDL2 fails (common on Windows):

```bash
pip install pygame
cp board_configs/pgdisplay/board_config.py src/lib/board_config.py
cd pydisplay/src
python3 -i path.py
```

## Input on desktop

Mouse events map to touch events. Same event API as on embedded targets.

## Next

- [Architecture](../concepts/architecture.md)
- [Examples catalog](../examples/index.md)
- [ESP32 deploy guide](esp32-board.md) — same API on hardware later

## Reference

- [API reference (core)](../reference/) → `displaysys`, `eventsys`
