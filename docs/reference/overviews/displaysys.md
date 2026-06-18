displaysys provides display driver classes (`BusDisplay`, `SDL2Display`, `PSDisplay`, …) with a unified drawing API based on MicroPython's `framebuf`.

## Narrative docs

- [Displays concept](../../concepts/displays.md) — pick a driver
- [Architecture](../../concepts/architecture.md) — how board_config wires the display
- [Display drivers (chips)](../../hardware/display-drivers.md) — st7789, ili9341, etc.

## Key entry points

- `DisplayDriver` — base class for all backends
- `BusDisplay` — SPI/I80 displays on MCUs
- `SDL2Display` / `PGDisplay` — desktop backends

Generated API pages for each module appear below (build time).
