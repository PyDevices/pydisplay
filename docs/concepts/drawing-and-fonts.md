# Drawing and fonts

**Start here for the `pygraphics` library:** [graphics](graphics.md) — quick start, FrameBuffer vs Draw, Area bounds, fonts, and loaders.

This page covers how `pygraphics` fits into the wider pydevices-examples stack.

## Which API?

| Need | Use |
|------|-----|
| Buffer + shapes + Area bounds | [`pygraphics`](graphics.md) — `FrameBuffer` or `Draw` |
| Basic pixels on a display | `framebuf` API on display or buffer |
| Peter Hinch scrollable buffer | `utils/displaybuf.DisplayBuffer` |
| CPython without importing add-ons | `pygraphics` (bundles pure-Python framebuf) |

See [Architecture](https://pydevices.github.io/pydevices/architecture.html).

## pygraphics module

`pygraphics` subclasses FrameBuffer and adds helpers (e.g. `round_rect`, `gradient_rect`). Methods return an **Area** object (`x`, `y`, `w`, `h`) describing the bounding box of what changed — useful for partial updates.

Use `Draw(canvas)` when you prefer a separate drawer object over subclassing.

## Font mechanisms

| Mechanism | Source | Notes |
|-----------|--------|-------|
| `pygraphics.text8` / `text14` / `text16` | Embedded romfont in `pygraphics` (`_font_8x*.py`) | Default; transparent; per-pixel on canvas — [patterns](graphics.md#choosing-a-font-rendering-pattern) |
| `pygraphics.Font(path, height)` | Romfont [`.bin` on disk](graphics.md#loading-romfont-bin-files-from-the-filesystem) | Optional; use with any pattern below |
| `pygraphics.Font(height=8)` | Embedded romfont for that height | Same bytes as `text8` / `text14` / `text16` |
| String FB + `blit_rect` | [`font_simpletest.py`](https://github.com/PyDevices/pydevices-examples/blob/main/src/examples/font_simpletest.py) (`string_blit` phase) | Opaque bg; low RAM; one blit per string — good desktop + tight MCU RAM |
| `Font.text(display_drv, …)` | [`font_simpletest.py`](https://github.com/PyDevices/pydevices-examples/blob/main/src/examples/font_simpletest.py) (`per_pixel` phase) | Transparent; lowest RAM; slowest on SPI |
| `DisplayBuffer` + `show(dirty)` | [`font_simpletest.py`](https://github.com/PyDevices/pydevices-examples/blob/main/src/examples/font_simpletest.py) (`displaybuf` phase) | Transparent; full-screen RAM; fastest repeated text on MCU |
| `tft_text.text()` | @russhughes text_font_converter | Width 8 or 16, height multiples of 8 |
| `tft_write.write()` | @russhughes write_font_converter | Proportional fonts |
| `framebuf.text()` | Damien `font_petme128_8x8` | MP framebuf API only; not romfont — see [Fonts in graphics](graphics.md#not-the-same-as-framebuftext) |

Peter Hinch's **Writer** (MicroPython-Touch) may be used on MicroPython but does not return Area objects.

## displaybuf.DisplayBuffer

Peter Hinch's API — full display as a logical framebuffer with 4/8/16-bit buffers drawing as 16-bit to the panel. Required for MicroPython-Touch; great for memory-constrained apps.

## API reference

[pygraphics source](https://github.com/PyDevices/pygraphics). [Utils API](../reference/utils/) → `displaybuf`.
