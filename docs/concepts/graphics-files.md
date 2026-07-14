# Graphics files

Two layers: **graphics package loaders** (eager, full image in RAM) and **pydisplay add-ons** (streaming and TFT-specific helpers).

## graphics package loaders

Built into [`graphics`](graphics.md):

| Function | Format |
|----------|--------|
| `graphics.bmp_to_framebuffer(path)` | Windows BMP → `FrameBuffer` |
| `graphics.pbm_to_framebuffer(path)` | PBM (1-bit) |
| `graphics.pgm_to_framebuffer(path)` | PGM (grayscale) |
| `graphics.load_image(path)` | Auto-detect PBM/PGM/BMP from header |
| `graphics.save_image(fb, path)` | Write PBM/PGM/BMP for supported formats |
| `graphics.FrameBuffer.from_file(path)` | Same as `load_image` |
| `graphics.FrameBuffer.save(path)` | Same as `save_image` |

### Save/load matrix

| Framebuffer format | File | Notes |
|--------------------|------|-------|
| `MONO_HLSB` | PBM (P4) | 1-bit portable bitmap |
| `GS2_HMSB` | PGM (P5, max 3) | 2-bit grayscale |
| `GS4_HMSB` | PGM (P5, max 15) | 4-bit grayscale |
| `GS8` | PGM (P5, max 255) | 8-bit grayscale |
| `RGB565` | BMP | 16-bit RGB565 Windows BMP |

`MONO_VLSB`, `MONO_HMSB`, and other display-native formats are not saved directly — convert or blit to a supported buffer first.

Use these for icons and sprites that fit in RAM on MCU or desktop.

## BMP565 (streaming)

`graphics.BMP565` reads/writes Windows BMP files in RGB565 format (export from GIMP). Shared header/row logic also powers `bmp_to_framebuffer` and `FrameBuffer.save()` for RGB565.

Features:

- Load entire file or **stream** slices for large images: `BMP565[1:5, 6:10]`
- Row mirroring for rotated scroll backgrounds
- Use an existing bytearray as buffer (screenshots)

Examples: `bmp565_simpletest.py`, `bmp565_sprite.py`, `bmp565_scroll.py`

## tft_text / tft_write bitmap helpers

From @russhughes st7789py_mpy:

- `.bitmap()` — decode `.py` image files from [image_converter.py](https://github.com/russhughes/st7789py_mpy/blob/master/utils/image_converter.py) or [sprites_converter.py](https://github.com/russhughes/st7789py_mpy/blob/master/utils/sprites_converter.py); renders full image then blits
- `.pbitmap()` — progressive line-at-a-time rendering with a one-line buffer

## PNG

Experimental support in add_ons — probe with [`tools/png_test.py`](https://github.com/PyDevices/pydisplay/blob/main/tools/png_test.py) (CPython only; requires `pypng` and a local checkout of [material-design-icons](https://github.com/google/material-design-icons) with its `png/` tree, or `PYDISPLAY_PNG_DIR`).
