displaysys provides display driver classes (`BusDisplay`, `SDLDisplay`, `PGDisplay`, `PSDisplay`, `JNDisplay`, `FBDisplay`) with a unified drawing API based on MicroPython's `framebuf`.

## Narrative docs

- [Displays concept](../../concepts/displays.md) — pick a driver
- [Display backend internals](../../concepts/display-backends.md) — GRAM/present, 565 API, color conversion
- [Architecture](../../concepts/architecture.md) — how board_config wires the display
- [Display drivers (chips)](../../hardware/display-drivers.md) — st7789, ili9341, etc.

## Key entry points

- `DisplayDriver` — base class for all backends
- `BusDisplay` — SPI/I80 displays on MCUs
- `SDLDisplay` / `PGDisplay` — desktop backends (SDL2 / PyGame)
- `PSDisplay` / `JNDisplay` — PyScript browser / Jupyter Notebook
- `FBDisplay` — CircuitPython framebuffer displays
- `display_drv.quit()` — release resources; called automatically by `Runtime` on quit

Generated API pages for each module appear below (build time).
