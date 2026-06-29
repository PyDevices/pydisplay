# graphics

Cross-platform 2D drawing: framebuf-compatible buffers, shape primitives that return **Area** bounds, fonts, and image loaders. One import works on MicroPython, CircuitPython, and CPython.

## Quick start

```python
import graphics

w, h = 16, 16
fb = graphics.FrameBuffer(bytearray(w * h * 2), w, h, graphics.RGB565)
fb.fill(0)
fb.fill_rect(1, 1, 6, 6, 0xFFFF)
fb.circle(8, 8, 3, 0x1234)
graphics.text8(fb, "Hi", 0, 0, 0xFFFF)
```

Inspect the runtime backend:

```python
print(graphics.capabilities())
# {"framebuf": "native" | "pure_python", "dialect": "...", "formats": [...]}
```

On CPython and CircuitPython, `graphics` bundles a pure-Python framebuf implementation — no add-ons required.

## FrameBuffer vs Draw vs module functions

| Style | When to use |
|-------|-------------|
| **`graphics.FrameBuffer`** | Default — own a buffer; get `.buffer`, `.width`, save/load, all shape methods |
| **`graphics.Draw(canvas)`** | Draw on a display driver or third-party object with `pixel` / `hline` / … |
| **Module functions** (`graphics.circle(fb, …)`) | Short scripts; same primitives as `FrameBuffer` methods |

```python
draw = graphics.Draw(display_drv)
draw.round_rect(5, 5, 50, 30, 4, 0xF800)
```

## Area and partial updates

Most draw methods return an `Area(x, y, w, h)` bounding box. Union dirty regions:

```python
a = fb.fill_rect(0, 0, 10, 10, color)
b = fb.circle(12, 12, 4, color)
dirty = a + b
display_drv.blit_rect(fb.buffer, dirty.x, dirty.y, dirty.w, dirty.h)
```

- **Setting** `fb.pixel(x, y, c)` returns `Area(x, y, 1, 1)`.
- **Reading** `fb.pixel(x, y)` returns the color (no `Area`).
- **`scroll()`** returns the full buffer bounds.

## Pixel formats

| Constant | Depth |
|----------|-------|
| `MONO_VLSB`, `MONO_HLSB`, `MONO_HMSB` | 1 bpp |
| `GS2_HMSB` | 2 bpp |
| `GS4_HMSB` | 4 bpp |
| `GS8` | 8 bpp |
| `RGB565` | 16 bpp |

`capabilities()["formats"]` lists names supported on this port.

## Fonts

Built-in heights: `text8`, `text14`, `text16`, or `Font(height=8)` with optional `.bin` romfont path.

```python
graphics.text8(fb, "Hello", 0, 0, 0xFFFF)
f = graphics.Font("/path/to/font8x14.bin", 14)
f.text(fb, "World", 0, 16, 0xFFFF)
```

Missing font files raise `FileNotFoundError`.

## Image loaders

Eager loaders in the `graphics` package (full image in RAM):

```python
fb = graphics.bmp_to_framebuffer("sprite.bmp")
fb = graphics.pbm_to_framebuffer("icon.pbm")
fb = graphics.pgm_to_framebuffer("gray.pgm")
fb = graphics.FrameBuffer.from_file("image.bmp")
```

`FrameBuffer.save()` writes PBM/PGM/BMP for supported formats (RGB565 and grayscale variants). Other formats raise `ValueError`.

For streaming/large BMP assets, use `graphics.BMP565` (sliceable, optional streaming reads) — see [Graphics files](graphics-files.md).

## pydisplay integration

| Need | Use |
|------|-----|
| Scrollable full-screen buffer | `add_ons/displaybuf.DisplayBuffer` |
| TFT proportional fonts | `tft_text` / `tft_write` add-ons |
| Large BMP sprites | `graphics.BMP565` |

See [Drawing and fonts](drawing-and-fonts.md) for the wider pydisplay drawing stack.

## FAQ

**Which framebuf am I using?** — `graphics.capabilities()["framebuf"]` is `native` on MicroPython MCU, `pure_python` on CPython.

**Draw method returned nothing?** — Use `graphics.FrameBuffer` or `Draw`; raw `framebuf.FrameBuffer` base methods do not return `Area`.

## Next

- [Graphics files](graphics-files.md) — loaders and BMP565
- [Displays](displays.md)
- [API reference](../reference/) → `graphics`
