# Tests

Self-contained tests for the standalone [`multimer`](../src/lib/multimer),
[`eventsys`](../src/lib/eventsys), [`graphics`](../src/lib/graphics), and
[`displaysys`](../src/lib/displaysys) packages.

They use only the Python standard library (`unittest`) — no third-party test
runner or build step is required. The shared bootstrap in
[`_env.py`](_env.py) puts `src/lib` on `sys.path`, so nothing needs to be
installed first.

On CPython the graphics package falls back to its pure-Python
`graphics._framebuf` implementation (the native `framebuf` module only exists
on MicroPython), so those tests exercise that fallback directly.

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

Or run a single module:

```bash
python -m unittest tests.test_ticks -v
# or
python tests/test_ticks.py
```

## What is covered

| Module | Area |
|--------|------|
| `test_ticks.py` | `ticks_ms` / `ticks_add` / `ticks_diff` / `ticks_less` / `sleep_ms` |
| `test_schedule.py` | `schedule` / `run_queued` and the `REQUIRES_RUN_QUEUED` flag |
| `test_timer.py` | the default `multimer.Timer` (whichever backend is selected) |
| `test_get_timer.py` | the `get_timer` convenience helper |
| `test_aio.py` | the opt-in `multimer.aio` asyncio timer |
| `test_events.py` | the `events` types/classes and `eventsys.custom_type` |
| `test_devices.py` | `Broker` and the `Queue`/`Touch`/`Encoder`/`Keypad` devices plus `devices.custom_type` |
| `test_keys.py` | the `Keys` key/modifier tables and `keyname`/`key`/`modname`/`mod` helpers |
| `test_area.py` | the `Area` rectangle helper (containment, overlap, transforms, protocols) |
| `test_framebuf.py` | the pure-Python `graphics._framebuf` fallback (pixels, fill, scroll) |
| `test_framebuf_plus.py` | the exported `graphics.FrameBuffer` (properties + `Area` returns) |
| `test_shapes.py` | the drawing primitives (`line`, `rect`, `circle`, `poly`, `blit`, ...) |
| `test_font.py` | `Font` and the `text` / `text8` / `text14` / `text16` helpers |
| `test_files.py` | `save` / `from_file` and the PBM/PGM converters |
| `test_draw.py` | the `Draw` canvas-binding wrapper |
| `test_color.py` | `color565` / `color565_swapped` / `color332` / `color_rgb` / `alloc_buffer` |
| `test_byteswap.py` | the `byteswap` helper (native or pure-Python fallback) |
| `test_display_driver.py` | the `DisplayDriver` base class: rotation, byte-swap controls, touch device, lifecycle and vertical scroll math |
| `test_fbdisplay.py` | the pure-Python `FBDisplay` driver (`fill_rect` / `blit_rect` / `pixel` / `fill` / `blit_transparent` / `show`) |
| `test_auto_refresh.py` | the optional `auto_refresh` timer wiring into `multimer` |
| `test_standalone.py` | proves each package imports and runs with **none** of the rest of pydisplay on the path |

The timer tests run on whichever synchronous backend the host selects
(`_ctypes`/`_ffi`/`_threading`/`_sdl2`/`_polling`); `_support.pump()` drives
them uniformly. Tests that need a real `machine.Timer` are skipped when no
backend is available.

The device tests drive each device through its `poll()` method using small
scripted `read` callbacks from [`_support.py`](_support.py), so they run
identically on every host without any hardware.

Graphics tests deliberately avoid the format paths that cannot work under
CPython's pure-Python fallback (for example `GS8` pixel writes), and focus on
the broad surface that behaves identically on MicroPython and CPython.

The displaysys driver tests run on plain CPython using a hardware-free
framebuffer (`_support.FakeFrameBuffer`) and a quiet-stdout helper. Tests that
need the optional `multimer` dependency are skipped when it is not importable.
