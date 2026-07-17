# pydisplay-graphics

Pure-Python `graphics` package for pydisplay — `FrameBuffer`, `Draw`, fonts, shapes, and image loaders. Import as `graphics`.

> **Pip name:** `pydisplay-graphics` · **Import:** `import graphics`

On desktop/Android when a native wheel is available, prefer [`graphics-cmod`](https://test.pypi.org/project/graphics-cmod/) (same import name, C implementation).

## Install

### CPython (TestPyPI)

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydisplay-graphics
```

### MicroPython (MIP)

```python
import mip
mip.install("graphics", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

## Quick start

```python
import graphics

fb = graphics.FrameBuffer(
    bytearray(160 * 128 * 2), 160, 128, graphics.RGB565
)
fb.fill(0)
fb.fill_rect(10, 10, 40, 40, 0xF800)
print(graphics.implementation())  # e.g. pydisplay_python
```

Higher-level drawing:

```python
from graphics import Draw, Area

draw = Draw(fb)
draw.rect(0, 0, 50, 50, 0x07E0)
draw.text8("hi", 2, 2, 0xFFFF)
```

## What you get

- `FrameBuffer` — framebuf-compatible surface with shapes, blit, and Area bounds
- `Draw` — clip stack and text helpers over a canvas
- Fonts (`text8`, `text14`, `text16`, `Font`) and loaders (`BMP565`, PBM/PGM/BMP helpers)
- `Area` geometry and module-level shape helpers

## Links

- [Documentation — graphics](https://pydisplay.readthedocs.io/en/latest/concepts/graphics/)
- [Documentation — Drawing and fonts](https://pydisplay.readthedocs.io/en/latest/concepts/drawing-and-fonts/)
- [Source](https://github.com/PyDevices/pydisplay)
- [Issues](https://github.com/PyDevices/pydisplay/issues)
- Related: [graphics-cmod](https://test.pypi.org/project/graphics-cmod/), [displaysys](https://test.pypi.org/project/displaysys/)

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydisplay/blob/main/LICENSE).
