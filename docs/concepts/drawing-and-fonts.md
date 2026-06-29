# Drawing and fonts

**Start here for the `graphics` library:** [graphics](graphics.md) — quick start, FrameBuffer vs Draw, Area bounds, fonts, and loaders.

This page covers how `graphics` fits into the wider pydisplay stack.

## Which API?

| Need | Use |
|------|-----|
| Buffer + shapes + Area bounds | [`graphics`](graphics.md) — `FrameBuffer` or `Draw` |
| Basic pixels on a display | `framebuf` API on display or buffer |
| Peter Hinch scrollable buffer | `add_ons/displaybuf.DisplayBuffer` |
| CPython without importing add-ons | `graphics` (bundles pure-Python framebuf) |

See [Architecture](architecture.md).

## graphics module

`graphics` subclasses FrameBuffer and adds helpers (e.g. `round_rect`, `gradient_rect`). Methods return an **Area** object (`x`, `y`, `w`, `h`) describing the bounding box of what changed — useful for partial updates and e-paper.

Use `Draw(canvas)` when you prefer a separate drawer object over subclassing.

## Font mechanisms

| Mechanism | Source | Notes |
|-----------|--------|-------|
| `graphics.Font` | Tony DiCola 5×7 lineage, romfont `.bin` files | 8×8, 8×14, 8×16 |
| `FrameBuffer` + `blit_rect` | Compose text in RAM, one blit to display | See [**pydisplay_demo**](../examples/pydisplay_demo.md) and `font_simpletest.py` |
| `tft_text.text()` | @russhughes text_font_converter | Width 8 or 16, height multiples of 8 |
| `tft_write.write()` | @russhughes write_font_converter | Proportional fonts |

Peter Hinch's **Writer** (MicroPython-Touch) may be used on MicroPython but does not return Area objects.

## displaybuf.DisplayBuffer

Peter Hinch's API — full display as a logical framebuffer with 4/8/16-bit buffers drawing as 16-bit to the panel. Required for MicroPython-Touch; great for memory-constrained apps.

## API reference

[API reference (core)](../reference/) → `graphics`. [Add-ons API](../reference/add_ons/) → `displaybuf`.
