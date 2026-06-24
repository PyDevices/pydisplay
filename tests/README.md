# Tests

Self-contained tests for the standalone [`displaysys`](../src/lib/displaysys) package.

They use only the Python standard library (`unittest`) — no third-party test
runner or build step is required. The shared bootstrap in
[`_env.py`](_env.py) puts `src/lib` on `sys.path`, so nothing needs to be
installed first.

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

Or run a single module:

```bash
python -m unittest tests.test_color -v
# or
python tests/test_color.py
```

## What is covered

| Module | Area |
|--------|------|
| `test_color.py` | `color565` / `color565_swapped` / `color332` / `color_rgb` / `alloc_buffer` |
| `test_byteswap.py` | the `byteswap` helper (native or pure-Python fallback) |
| `test_display_driver.py` | the `DisplayDriver` base class: rotation, byte-swap controls, touch device, lifecycle and vertical scroll math |
| `test_fbdisplay.py` | the pure-Python `FBDisplay` driver (`fill_rect` / `blit_rect` / `pixel` / `fill` / `blit_transparent` / `show`) |
| `test_auto_refresh.py` | the optional `auto_refresh` timer wiring into `multimer` |
| `test_standalone.py` | proves `displaysys` imports and runs with **none** of the rest of pydisplay on the path |

The driver tests run on plain CPython using a hardware-free framebuffer
(`_support.FakeFrameBuffer`) and a quiet-stdout helper. Tests that need the
optional `multimer` dependency are skipped when it is not importable.
