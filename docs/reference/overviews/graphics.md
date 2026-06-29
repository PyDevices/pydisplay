graphics extends `framebuf` with extra drawing helpers (rounded rectangles, gradients, polygons) and returns **Area** bounding boxes for partial updates.

## Narrative docs

- [graphics concept](../../concepts/graphics.md) — quick start, FrameBuffer vs Draw, capabilities
- [Drawing and fonts](../../concepts/drawing-and-fonts.md) — pydisplay drawing stack
- [Graphics files](../../concepts/graphics-files.md) — loaders and BMP565

## Key entry points

- `graphics.FrameBuffer` — framebuf subclass with shape helpers and Area returns
- `graphics.Draw` — draws on any framebuf-compatible canvas
- `graphics.Area` — dirty rectangle with union/clip helpers
- `graphics.capabilities()` — `native` vs `pure_python` framebuf backend
- Module functions — `circle`, `rect`, `text8`, … (same primitives as FrameBuffer)
- `bmp_to_framebuffer`, `pbm_to_framebuffer`, `pgm_to_framebuffer` — image loaders
- `BMP565` — sliceable/streaming RGB565 BMP asset

Generated API pages for each module appear below (build time).
