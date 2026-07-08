# Display backend internals

This document explains how pydisplay **display drivers** relate to each other: the
shared **565 API contract**, the **two-stage draw/present** model used by desktop
and browser simulators, **color conversion** strategies, and why each backend
chose its implementation pattern.

For a shorter “which driver do I pick?” guide, see [Displays](displays.md). For
chip wiring and board configs, see [Board configs](../hardware/board-configs.md)
and [Display interfaces](../hardware/display-interfaces.md).

## The DisplayDriver API contract

Application and example code assume a **16-bit RGB565** surface:

- `display_drv.color_depth == 16` (bits per pixel)
- Color literals like `0xFFFF`, `0xF800`, and helpers like `color565(r, g, b)`
- Scratch buffers: `FrameBuffer(..., RGB565)` and
  `BPP = display_drv.color_depth // 8` (2 bytes per pixel)
- `blit_rect` source buffers sized `w * h * 2`
- `blit_transparent` key colors as 2-byte 565 values

**BusDisplay**, **FBDisplay**, and most TFT paths are **565 end-to-end** — the
API matches the hardware framebuffer.

Other backends store pixels in a **deeper native format** (RGB888 strip buffer,
PIL RGB, canvas RGBA, SDL texture at 24/32 bpp). They still expose the **565
API** and convert at draw time via `color_rgb` (or backend-specific blit paths).

### Color encoding trap

565 and 888 use **different integer layouts**:

| Meaning | RGB565 int | RGB888 int |
|---------|------------|------------|
| White | `0xFFFF` | `0xFFFFFF` |
| Red | `0xF800` | `0xFF0000` |

RGB888 unpack (used by `PixelFramebuffer` and `graphics.RGB888`) treats the int
as `0xRRGGBB`. Passing `0xFFFF` (565 white) through that path yields cyan
(R=0, G=255, B=255), not white.

The shared expand helper is **`color_rgb()`** in `displaysys/__init__.py`: 565
int or 2-byte little-endian slice → `(r, g, b)` with 5/6/5 bit expansion. Tests
live in `tests/test_color.py`.

## Two-stage architecture: logical GRAM + present

Four simulators — **SDLDisplay**, **PGDisplay**, **PSDisplay**, **JNDisplay**
— mimic an **ILI9341-style** panel:

```text
  App draw API                Present path
  ─────────────               ──────────────
  fill_rect / blit_rect  →    self._buffer   (logical GRAM)
                              render()       (scroll bands, scale, …)
                              show()         (flip / widget / canvas)
```

1. **`self._buffer`** — offscreen memory at logical `width × height` (PG calls
   this “the LCD’s internal memory”).
2. **Draw methods** — write only into that buffer.
3. **`render()`** — composes the buffer to the visible surface, including
   **vertical scroll** (top fixed / scroll area / bottom fixed).
4. **`show()`** — pushes frames to the OS window, browser canvas, or Jupyter
   widget.

Scroll emulation **requires** this split: you cannot draw directly on the window
and still implement `vscroll` / `set_vscroll` correctly. See
[pydisplay_demo](../examples/pydisplay_demo.md) for the redraw-at-`vscroll=0`
rule.

**PixelDisplay** is different: there is no ILI9341 scroll model. Drawing updates
an RGB888 grid buffer; `show()` diff-flushes to the LED strip.

### Vertical scroll (shared by SDL / PG / PS / JN)

All four implement the same band compositing in `render()`:

- **TFA** — top fixed area (pinned rows)
- **VSA** — vertical scroll area (content that moves)
- **BFA** — bottom fixed area

`display_drv.set_vscroll(tfa, bfa)` and the `vscroll` property map to the
controller-style `vscsad` address. On **SDLDisplay**, `render()` uses multiple
`SDL_RenderCopy` bands (a single full-frame copy was disabled due to platform
issues). **PGDisplay** and **PSDisplay** use the same four-step blit/drawImage
layout when scrolled.

### Rotation

| Backend | Buffer rotation |
|---------|-----------------|
| **SDLDisplay** | `_rotation_helper` — new SDL texture + `SDL_RenderCopyEx` |
| **PGDisplay** | `_rotation_helper` — `pg.transform.rotate` on `_buffer` |
| **PSDisplay** | `_rotation` tracked; **no** `_rotation_helper` (surface dims swap only) |
| **JNDisplay** | Same as PS — property only, no pixel rotation |
| **PixelDisplay** | `rotation` on inner framebuf (grid wiring), not LCD-style |

Full rotation matters for **SDL/PG** desktop LCD simulation. Browser and notebook
backends document that rotation reshapes the surface but does not rotate pointer
coordinates — see [Displays — Browser / notebook](displays.md#browser--notebook-pyscript-jupyter).

### Scaling

| Backend | Mechanism |
|---------|-----------|
| **PGDisplay** | Constructor `scale`; `pg.transform.scale_by` at present; `touch_scale = scale` |
| **SDLDisplay** | Window size `width * scale`; `SDL_RenderSetLogicalSize` for logical coords |
| **PSDisplay** | CSS layout vs canvas pixel size; `_pointer_scale()` / `touch_scale` |
| **JNDisplay** | 1:1 (`touch_scale = 1.0`) |
| **PixelDisplay** | N/A (tiny physical grid) |

## Why each backend exists (runtime)

| Backend | Typical runtime | Why it exists |
|---------|-----------------|---------------|
| **SDLDisplay** | CPython, MicroPython Unix, CircuitPython Unix | Native SDL2 / `usdl2`; default on MP Unix |
| **PGDisplay** | CPython desktop | Easier install on Windows; avoids some SDL glitches on Chromebooks; default in `lib/board_config.py` when pygame imports |
| **PSDisplay** | PyScript | HTML Canvas 2D; no SDL/pygame in the browser |
| **JNDisplay** | Jupyter | `ipywidgets` / PNG refresh; interactive `JNDevices` |
| **PixelDisplay** | MCU / CP | NeoPixel / DotStar grids via `displaysys.pixeldisplay` |

CircuitPython Unix **SDLDisplay** forces **software rendering** when accelerated
GL cannot attach rotated render targets (see comment in `sdldisplay.py`).
MicroPython SDL **`show()`** may defer present on `MemoryError` when the heap is
locked during scroll rendering.

## Color conversion toolbox

Backends use several patterns to map **565 API input** to **native storage**:

| Pattern | Where | Description |
|---------|-------|-------------|
| **Bitwise expand** | `color_rgb()` | Per-color 565 → `(r,g,b)`; fills and single pixels |
| **LUT-assisted loop** | **PSDisplay** | 65536 × 4 byte table; blit loop indexes LUT → RGBA for `putImageData` |
| **Python pixel loop** | **PGDisplay** blit, **JNDisplay** blit | Per pixel: read 2 bytes → `color_rgb` → `set_at` / PIL `point` |
| **Zero-copy passthrough** | **SDLDisplay** at 16 bpp | `SDL_UpdateTexture` with 565 pitch — buffer format matches texture |
| **Raw 565 pack** | **BusDisplay**, **FBDisplay** | `(c & 0xFFFF).to_bytes(2, …)` — no expand |

Not yet centralized in `displaysys`, but useful for future shared helpers:

- **`frombuffer` + blit** (Pygame) — `pg.image.frombuffer(buf, (w,h), "RGB565")`
  then `dest.blit(src, (x,y))` for **16-in / 16-stored** without a Python loop
- **Row expand** — convert one row of 565 to RGB/RGBA, bulk-write
- **Component mini-LUTs** — small 5/6/5-bit tables (~128 bytes) instead of 256 KB

### Per-backend blit strategy (today)

| Backend | Native sink | Blit path | Rationale |
|---------|-------------|-----------|-----------|
| **SDLDisplay** (16) | RGB565 texture | Zero-copy upload | Throughput on large blits; matches app buffers |
| **SDLDisplay** fill | Same texture | `color_rgb` → SDL RGB draw | Draw API expects 8-bit RGB |
| **PGDisplay** | Pygame surface (default 16) | Per-pixel `set_at` loop | Simple; partial `renderRect`; room to switch to `frombuffer`+`blit` |
| **PSDisplay** | Canvas RGBA | LUT → `ImageData` | Browser API requires RGBA bytes; large blits |
| **JNDisplay** | PIL RGB | Loop → `pixel` | Present is PNG-bound; blit speed secondary |
| **PixelDisplay** | RGB888 strip buf | 565 in → `color_rgb` → inner 888 | Tiny grids; standard DisplayDriver API |

### SDL vs Pygame “fast path”

**SDL** at `color_depth=16` is true **16-in / 16-stored** for blits: the app’s
565 buffer is uploaded directly into a RGB565 render-target texture.

**Pygame** can match that intent (not the same mechanism) by keeping a 16-bit
surface and using **`frombuffer` + `blit`** once per `blit_rect` call instead of
`set_at` per pixel. The current PG implementation still expands each pixel to
RGB for `set_at`, which quantizes back to 565 on a 16-bit surface — correct but
slow at 320×480.

### LUT size and MCUs

**PSDisplay** allocates **65536 × 4 ≈ 256 KB** for `_rgba_lut` — appropriate
in PyScript, **not** on typical MCUs (e.g. RP2040 has 264 KB SRAM total).

For **PixelDisplay** (8×4, 12×6, …), a **`color_rgb` loop** over tens or hundreds
of pixels is negligible. A full 565→888 LUT (~192 KB for 3-byte entries) would
cost more RAM than the grid itself.

## PixelDisplay specifics

Addressable LED boards wire:

```python
_pixel_framebuf = PixelFramebuffer(...)  # internal; RGB888 grid + strip map
display_drv = PixelDisplay(_pixel_framebuf)
```

**Use `display_drv` for all app drawing.** `_pixel_framebuf` is prefixed to
discourage bypassing the DisplayDriver API (see
[Board configs — Pixel configs](../hardware/board-configs.md#pixel--addressable-led-configs)).

`PixelDisplay` exposes the usual **565 `DisplayDriver` API** (`color_depth=16`).
The inner `PixelFramebuffer` stays **RGB888** for the strip; `fill_rect`,
`pixel`, and `blit_rect` expand via `color_rgb` before writing the inner buffer.

MicroPython uses `displaysys.pixeldisplay.PixelFramebuffer`; CircuitPython uses
Adafruit `adafruit_pixel_framebuf` behind the same `PixelDisplay` wrapper.

## Hardware drivers (brief)

These follow the 565 API without a separate “present” stage in the same sense:

| Class | Storage | Notes |
|-------|---------|-------|
| **BusDisplay** | Panel GRAM via SPI/I80 | Optional byteswap; true 565 |
| **FBDisplay** | CircuitPython framebuf | RAM mirror + `refresh()` |
| **BoardDisplay** | displayio Bitmap | 565 buffer → bitmap on `show()` |
| **EPaperDisplay** | 1/2/4 bpp packed | `color_depth` matches panel |

## Consolidation direction

Goals discussed for displaysys maintenance:

1. **One API** — all `DisplayDriver` instances report `color_depth=16` and accept
   565 colors and blit buffers unless the hardware is genuinely sub-16-bit
   (e-paper).
2. **Shared conversion helpers** in `displaysys/__init__.py` — `color_rgb`
   (exists), plus swappable **loop** vs **LUT** blit writers for benchmarking.
3. **Keep backend-specific fast paths** where they matter:
   - SDL: zero-copy 565 blit
   - PS: LUT for RGBA canvas
   - PG: consider `frombuffer`+`blit` for 565 surfaces
   - PixelDisplay: loop expand (tiny grids)
4. **Lazy LUT** — build only on CPython / desktop unless explicitly enabled, so
   MCUs never allocate 256 KB silently.

Internal buffer format may remain 565 (SDL), RGB (JN), RGBA (PS), or RGB888
(strip) as long as the **public** contract stays 565.

## Related reading

- [Displays](displays.md) — pick a driver, input, scroll overview
- [pydisplay_demo](../examples/pydisplay_demo.md) — scroll bands and redraw rules
- [Architecture](architecture.md) — how `board_config` wires drivers
- [Display interfaces](../hardware/display-interfaces.md) — hardware taxonomy
- `tests/test_color.py` — `color_rgb` / `color565` contract tests
