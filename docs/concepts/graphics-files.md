# Graphics files

Two layers: **graphics package loaders** (eager, full image in RAM) and **pydisplay add-ons** (streaming and TFT-specific helpers).

## graphics package loaders

Built into [`graphics`](graphics.md):

| Function | Format |
|----------|--------|
| `graphics.bmp_to_framebuffer(path)` | Windows BMP → `FrameBuffer` |
| `graphics.pbm_to_framebuffer(path)` | PBM (1-bit) |
| `graphics.pgm_to_framebuffer(path)` | PGM (grayscale) |
| `graphics.FrameBuffer.from_file(path)` | Auto-detect PBM/PGM/BMP from header |
| `graphics.FrameBuffer.save(path)` | Write PBM/PGM/BMP for supported formats |

Use these for icons and sprites that fit in RAM on MCU or desktop.

## add_ons: BMP565 (streaming)

Class in `add_ons/bmp565.py` — reads/writes Windows BMP files in RGB565 format (export from GIMP).

Features:

- Load entire file or **stream** slices for large images: `BMP565[1:5, 6:10]`
- Row mirroring for rotated scroll backgrounds
- Use an existing bytearray as buffer (screenshots)

Examples: `bmp565_simpletest.py`, `bmp565_sprite.py`, `bmp565_scroll.py`

BMP565 and `bmp_to_framebuffer` both parse RGB565 BMP; consolidation into shared internals is planned as a follow-up.

## tft_text / tft_write bitmap helpers

From @russhughes st7789py_mpy:

- `.bitmap()` — decode `.py` image files from [image_converter.py](https://github.com/russhughes/st7789py_mpy/blob/master/utils/image_converter.py) or [sprites_converter.py](https://github.com/russhughes/st7789py_mpy/blob/master/utils/sprites_converter.py); renders full image then blits
- `.pbitmap()` — progressive line-at-a-time rendering with a one-line buffer

## PNG

Experimental support in add_ons — see [`png_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/png_test.py) (CPython only; requires `pypng` and a checkout of [material-design-icons](https://github.com/google/material-design-icons) at `~/github/material-design-icons/png/`).
