graphics extends `framebuf` with extra drawing helpers (rounded rectangles, gradients, polygons) and returns **Area** bounding boxes for partial updates.

## Narrative docs

- [Drawing and fonts](../../concepts/drawing-and-fonts.md) — framebuf vs graphics vs Draw
- [Graphics files](../../concepts/graphics-files.md) — BMP, PBM loaders

## Key entry points

- `FrameBuffer` — framebuf subclass with shape helpers
- `Draw` — draws on any canvas (display or buffer)
- `_shapes` module functions — low-level primitives (also used by `Draw`)

Generated API pages for each module appear below (build time).
