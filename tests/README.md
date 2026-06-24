# Tests

Self-contained tests for the standalone [`graphics`](../src/lib/graphics) package.

They use only the Python standard library (`unittest`) — no third-party test
runner or build step is required. The shared bootstrap in
[`_env.py`](_env.py) puts `src/lib` on `sys.path`, so nothing needs to be
installed first.

On CPython the package falls back to its pure-Python `graphics._framebuf`
implementation (the native `framebuf` module only exists on MicroPython), so
these tests exercise that fallback directly.

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

Or run a single module:

```bash
python -m unittest tests.test_area -v
# or
python tests/test_area.py
```

## What is covered

| Module | Area |
|--------|------|
| `test_area.py` | the `Area` rectangle helper (containment, overlap, transforms, protocols) |
| `test_framebuf.py` | the pure-Python `graphics._framebuf` fallback (pixels, fill, scroll) |
| `test_framebuf_plus.py` | the exported `graphics.FrameBuffer` (properties + `Area` returns) |
| `test_shapes.py` | the drawing primitives (`line`, `rect`, `circle`, `poly`, `blit`, ...) |
| `test_font.py` | `Font` and the `text` / `text8` / `text14` / `text16` helpers |
| `test_files.py` | `save` / `from_file` and the PBM/PGM converters |
| `test_draw.py` | the `Draw` canvas-binding wrapper |
| `test_standalone.py` | proves `graphics` imports and runs with **none** of the rest of pydisplay on the path |

Tests deliberately avoid the format paths that cannot work under CPython's
pure-Python fallback (for example `GS8` pixel writes), and focus on the broad
surface that behaves identically on MicroPython and CPython.
