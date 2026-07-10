graphics extends `framebuf` with extra drawing helpers (rounded rectangles, gradients, polygons) and returns **Area** bounding boxes for partial updates.

## Narrative docs

- [graphics concept](../../concepts/graphics.md) — quick start, font rendering patterns, loaders
- [Drawing and fonts](../../concepts/drawing-and-fonts.md) — pydisplay drawing stack
- [Graphics files](../../concepts/graphics-files.md) — loaders and BMP565

## Key entry points

- `graphics.FrameBuffer` — subclass of the bundled `graphics.framebuf.FrameBuffer` with shape helpers and Area returns (same implementation on every runtime)
- `graphics.Draw` — draws on any framebuf-compatible canvas
- `graphics.Area` — dirty rectangle with union/clip helpers
- Module functions — `circle`, `rect`, `text8`, … (same primitives as FrameBuffer)
- `graphics.Font` — romfont renderer; built-in embedded fonts or optional `.bin` path ([Fonts](../../concepts/graphics.md#fonts))
- `load_image`, `save_image` — auto-detect load / format-aware save
- `bmp_to_framebuffer`, `pbm_to_framebuffer`, `pgm_to_framebuffer` — image loaders
- `BMP565` — sliceable/streaming RGB565 BMP asset

Generated API pages for each module appear below (build time).
