# Drawing and fonts

## framebuf everywhere

All drawing targets support MicroPython's `framebuf.FrameBuffer` methods: `pixel`, `hline`, `vline`, `line`, `rect`, `fill_rect`, `text`, `blit`, etc.

CPython and CircuitPython lack a compatible built-in `framebuf` — use `add_ons/framebuf.py`.

## graphics module

`graphics` subclasses FrameBuffer and adds helpers (e.g. `round_rect`). Methods return an **Area** object (`x`, `y`, `w`, `h`) describing the bounding box of what changed — useful for partial updates and e-paper (future).

## Font mechanisms

| Mechanism | Source | Notes |
|-----------|--------|-------|
| `graphics.Font` | Tony DiCola 5×7 lineage, romfont `.bin` files | 8×8, 8×14, 8×16 |
| `tft_text.text()` | @russhughes text_font_converter | Width 8 or 16, height multiples of 8 |
| `tft_write.write()` | @russhughes write_font_converter | Proportional fonts |
| `EZFont` | microPyEZfonts / font-to-py | In `src/utils/`; no Area return |

Peter Hinch's **Writer** (MicroPython-Touch) may be used on MicroPython but does not return Area objects.

## displaybuf.DisplayBuffer

Peter Hinch's API — full display as a logical framebuffer with 4/8/16-bit buffers drawing as 16-bit to the panel. Required for MicroPython-Touch; great for memory-constrained apps.

## API reference

[Package Reference](../reference/) → `graphics`, `framebuf` ([add-ons reference](../reference/add_ons/)).
