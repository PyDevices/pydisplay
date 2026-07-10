# Tests

Self-contained tests for in-tree [`multimer`](../src/lib/multimer),
[`eventsys`](../src/lib/eventsys), [`graphics`](../src/lib/graphics), and
[`displaysys`](../src/lib/displaysys) packages.

They use only the Python standard library (`unittest`) — no third-party test
runner or build step is required. The shared bootstrap in
[`_env.py`](_env.py) puts `src/lib` on `sys.path`, so nothing needs to be
installed first.

`graphics.FrameBuffer` always builds on the bundled pure-Python
`graphics.framebuf` module (never the native `framebuf` module compiled into
MicroPython/CircuitPython firmware), so the same implementation is exercised
on every runtime.

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

Or run a single module:

```bash
python -m unittest discover -s tests -p 'test_multimer.py' -v
# or
python tests/test_multimer.py
```

## What is covered

| Module | Area |
|--------|------|
| `test_multimer.py` | public multimer API (`Timer`, `AsyncTimer`, `schedule`, `sleep_ms`, and `ticks_*`) |
| `test_events.py` | the `events` types/classes and `eventsys.register_event` |
| `test_devices.py` | `Broker` and the `Queue`/`Touch`/`Encoder`/`Keypad` devices plus `register_device` |
| `test_joystick.py` | `JoystickDevice` with a mock driver |
| `test_keys.py` | the `Keys` key/modifier tables and `keyname`/`key`/`modname`/`mod` helpers |
| `test_area.py` | the `Area` rectangle helper (containment, overlap, transforms, protocols) |
| `test_blit_hooks.py` | blit dispatch to display hooks and framebuffer fast paths |
| `test_clip.py` | clip helpers and ``ClippedCanvas`` |
| `test_framebuf.py` | the MP-parity `add_ons/framebuf` module (pixels, fill, scroll, text, blit, poly) |
| `test_framebuf_sync.py` | generated `graphics/framebuf.py` matches canonical `add_ons/framebuf.py` |
| `test_framebuf_plus.py` | the exported `graphics.FrameBuffer` (properties + `Area` returns) |
| `test_shapes.py` | the drawing primitives (`line`, `rect`, `circle`, `poly`, `blit`, ...) |
| `test_font.py` | `Font` and the `text` / `text8` / `text14` / `text16` helpers |
| `test_files.py` | `save` / `from_file` and the PBM/PGM converters |
| `test_draw.py` | the `Draw` canvas-binding wrapper |
| `test_color.py` | `color565` / `color565_swapped` / `color332` / `color_rgb` / `alloc_buffer` |
| `test_byteswap.py` | the `byteswap` helper (native or pure-Python fallback) |
| `test_display_driver.py` | the `DisplayDriver` base class: rotation, byte-swap controls, touch device, lifecycle and vertical scroll math |
| `test_fbdisplay.py` | the pure-Python `FBDisplay` driver (`fill_rect` / `blit_rect` / `pixel` / `fill` / `blit_transparent` / `show`) |
| `test_auto_refresh.py` | placeholder while `auto_refresh` migrates to `Timer` / `AsyncTimer` |
| `test_standalone.py` | proves each package imports and runs with **none** of the rest of pydisplay on the path |

The multimer tests exercise the public package contract. Private backend
modules are not part of the default test surface.

The device tests drive each device through its `poll()` method using small
scripted `read` callbacks from [`_support.py`](_support.py), so they run
identically on every host without any hardware.

Graphics tests exercise every `framebuf` format (`MONO_VLSB`, `MONO_HLSB`,
`MONO_HMSB`, `RGB565`, `GS2_HMSB`, `GS4_HMSB`, `GS8`) against the single
bundled `graphics.framebuf` implementation, which is verified byte-for-byte
against the real MicroPython `framebuf` C module (fuzz-tested; see
`test_framebuf.py`).

The displaysys driver tests run on plain CPython using a hardware-free
framebuffer (`_support.FakeFrameBuffer`) and a quiet-stdout helper. Tests that
need the optional `multimer` dependency are skipped when it is not importable.
