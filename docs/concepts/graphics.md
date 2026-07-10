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

`graphics` bundles its own pure-Python `framebuf` implementation (`graphics.framebuf`, MP-parity
with `modframebuf.c`) and always builds `graphics.FrameBuffer` on top of it — the same code path
runs on MicroPython, CircuitPython, and CPython, so there is no native-vs-pure-Python backend to
inspect or branch on.

## FrameBuffer vs Draw vs module functions

| Style | When to use |
|-------|-------------|
| **`graphics.FrameBuffer`** | Default — own a buffer; get `.buffer`, `.width`, save/load, all shape methods |
| **`graphics.Draw(canvas)`** | Draw on a display driver or third-party object with `pixel` / `hline` / … |
| **Module functions** (`graphics.circle(fb, …)`) | Short scripts; same primitives as `FrameBuffer` methods |

```python
draw = graphics.Draw(display_drv)
draw.round_rect(5, 5, 50, 30, 4, 0xF800)

with draw.clip(10, 20, 100, 60):
    draw.fill_rect(0, 0, 200, 200, 0xF800)  # only the intersection is drawn
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
fb = graphics.load_image("image.bmp")  # or FrameBuffer.from_file(...)
```

`save_image(fb, path)` and `FrameBuffer.save()` write PBM/PGM/BMP for the formats in [Graphics files](graphics-files.md). Other framebuffer formats raise `ValueError`.

## Blit fast paths

`graphics.blit()`, `Draw.blit()`, and `blit_rect()` dispatch to faster implementations when available:

| Destination | Fast path |
|-------------|-----------|
| Display driver (`blit_rect` / `blit_transparent`) | SPI/SDL/pygame bulk copy |
| `FrameBuffer` | `graphics.framebuf`'s `blit()` (same implementation on every runtime) |

Use `Draw(display_drv).blit(sprite_fb, x, y)` instead of a per-pixel loop — it routes to `display_drv.blit_rect` for RGB565 sprites.

### Clip regions

`Draw.clip(x, y, w, h)` (or `clip(Area(...))`) is a context manager that intersects all drawing with a rectangle. Nested clips intersect further; the clip is restored when the block exits:

```python
with draw.clip(10, 10, 50, 40):
    draw.fill(0x0000)          # fills only the clip rect
    draw.text8("Panel", 0, 0, 0xFFFF)
```

For streaming/large BMP assets, use `graphics.BMP565` (sliceable, optional streaming reads) — see [Graphics files](graphics-files.md).

## pydisplay integration

| Need | Use |
|------|-----|
| Scrollable full-screen buffer | `add_ons/displaybuf.DisplayBuffer` |
| TFT proportional fonts | `tft_text` / `tft_write` add-ons |
| Large BMP sprites | `graphics.BMP565` |

See [Drawing and fonts](drawing-and-fonts.md) for the wider pydisplay drawing stack.

## FAQ

**Draw method returned nothing?** — Use `graphics.FrameBuffer` or `Draw`; the bare `graphics.framebuf.FrameBuffer` base methods do not return `Area`.

## Next

- [Graphics files](graphics-files.md) — loaders and BMP565
- [Displays](displays.md)
- [API reference](../reference/) → `graphics`
