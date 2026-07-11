# Examples catalog

All examples live in [`src/examples/`](https://github.com/PyDevices/pydisplay/tree/main/src/examples/).

```python
mip.install("github:PyDevices/pydisplay/packages/examples.json", target="./examples")
```

Use `import lib.path` first in a development clone (see [full clone](../installation/full-clone.md)).

!!! tip "Start here"
    New to pydisplay? Copy the [**App starter**](app-starter.md) boilerplate to begin your first app, then read the [**pydisplay_demo** guide](pydisplay_demo.md) for rotation, scrolling, and buffered text.

## PyScript gallery markers

Examples that appear in the [browser gallery](https://PyDevices.github.io/pydisplay/pyscript/) carry a header comment used by `scripts/pyscript_gen_packages.py`:

```python
# pyscript gallery: all
```

| Tag | Gallery section |
|-----|-----------------|
| `async` | Async demos (asyncio / `dual_main` / `timer_async`) |
| `all` | Blocking or dual-path demos that still run after **Run** in the browser |

Omit the marker (or use `# pyscript skip: gallery`) to keep a script out of the card grid. Binary-dependent demos use `# pyscript binaries:` and are excluded automatically. See [PyScript local development](../guides/pyscript.md).

### Search commands

```bash
rg '^# pyscript gallery:' src/examples/
rg '^# pyscript gallery: async' src/examples/
rg '^# pyscript gallery: all' src/examples/
```

### Canonical patterns

**Quit-aware poll loop** — [`hello.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/hello.py), [`scroll.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/scroll.py), [`displaysys_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/displaysys_simpletest.py):

```python
from board_config import display_drv, runtime

while True:
    if runtime is not None:
        runtime.poll()
    ...  # draw
    display_drv.show()
    if runtime is not None and runtime.quit_requested:
        return
    sleep_ms(1)
```

Or dispatch all events and break on `events.QUIT` (see `displaysys_simpletest.py`).

**`run_forever` with poll** — [`pydisplay_demo.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/pydisplay_demo.py), [`calculator.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/calculator.py):

```python
from multimer import run_forever
import eventsys

def handle_events():
    if elist := runtime.poll():
        for e in elist:
            if e.type == eventsys.QUIT:
                return True
            ...
    return False

run_forever(handle_events, delay_ms=20)
```

**Event-driven poll** — [`eventsys_encoder_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/eventsys_encoder_test.py):

```python
display_drv.show()  # after initial draw
while True:
    if elist := runtime.poll():
        for e in elist:
            ...  # draw on event
            display_drv.show()
```

**Forever LVGL / library-driven app** — [`lv_test_timer.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer.py): follows `runtime.timer_async` via `dual_main` (no env vars). Sync path uses a cooperative deadline/`time.sleep` loop; async path uses `await asyncio.sleep(0)` plus `runtime.poll()`.

**`tft_config` animation / one-shot** — subdirectory demos [`alien/alien.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/alien/alien.py), [`tiny_toasters/tiny_toasters.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tiny_toasters/tiny_toasters.py), [`chango/chango.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/chango/chango.py):

```python
from board_config import runtime

tft.show()
if runtime is not None:
    runtime.poll()  # SDL message pump — required on MicroPython Windows
```

Without `runtime.poll()`, the SDL window can freeze after the first frame even when the Python loop keeps running.

**LVGL apps** — [`lv_test_timer.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer.py): import `display_driver` from sync/async entrypoints and drive the loop with `dual_main` (follows `runtime.timer_async`). See [LVGL guide](../guis/lvgl.md).

**PyWidgets (pdwidgets)** — [`widgets_stub.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/widgets_stub.py): build UI, then:

```python
import pdwidgets as pd

pd.init_timer(10)  # optional; sets poll delay for run_forever
# ... widgets ...
pd.run_forever()
```

`run_forever()` calls `pd.tick()` each frame then polls the runtime. During setup bursts before `run_forever()`, call `pd.tick()` to flush draws. See [PyWidgets](../guis/pywidgets.md#event-loop).

### Notes

- `displaysys_simpletest.py` handles `events.QUIT` in its poll loop. Same quit pattern as [`scroll_touch_test_displaybuf.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/scroll_touch_test_displaybuf.py).
- `font_simpletest.py` — string-sized `FrameBuffer`, opaque background, one `blit_rect` per draw (see [Font rendering patterns](../concepts/graphics.md#choosing-a-font-rendering-pattern)).
- `font_simpletest2.py` — `Font.text(display_drv, …)`; transparent, per-pixel (slowest bus pattern).
- `font_simpletest3.py` — `DisplayBuffer` + `show(dirty)`; transparent, best when RAM allows a full-screen buffer.
- `nano_gui_simpletest.py` requires upstream [`gui/`](../guis/nano-gui.md) in `add_ons/`.
**Legend:** Platforms = CPython · MCU · PyScript · Wokwi · Packages = core · add_ons · LVGL

## Suggested learning order

| Step | Script | Platforms | Packages | Screenshot |
|------|--------|-----------|----------|------------|
| 0 | [**App starter**](app-starter.md) (doc boilerplate) | CPython · MCU · PyScript | core | — |
| 1 | [`pydisplay_demo.py`](pydisplay_demo.md) | CPython · MCU | core | — |
| 2 | `color_test.py` | CPython · MCU | core | [color_test](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/color_test.png) |
| 3 | `displaysys_simpletest.py` | CPython · MCU | core | — |
| 4 | `eventsys_simpletest.py` | CPython · MCU · PyScript | core | — |
| 5 | `framebuf_simpletest.py` | CPython · MCU | core | [framebuf](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/framebuf_simpletest.png) |
| 6 | `graphics_simpletest.py` | CPython · MCU | core | [shapes](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/shapes_simpletest.png) |
| 7 | `eventsys_touch_test.py` | CPython · MCU | core | — |
| 8 | `calculator.py` | CPython · PyScript | core | [calculator](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/calculator.png) |
| 9 | `paint.py` | CPython · PyScript | core | [paint](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/paint.png) |
| 10 | `widgets_simpletest.py` | CPython · MCU | add_ons | — |

PyScript requires asyncio — see [PyScript asyncio guide](../guides/pyscript-asyncio.md).

## Hello and basics

| Resource | Description | Platforms | Packages |
|----------|-------------|-----------|----------|
| [**App starter**](app-starter.md) | Copy-paste app boilerplate (doc only) | CPython · MCU · PyScript | core |
| [`pydisplay_demo.py`](pydisplay_demo.md) | Clicks, rotation, scroll (`board_config` + multimer) | CPython · MCU | core |
| `pydisplay_demo_async.py` | Same as pydisplay_demo with `multimer` | CPython · MCU · PyScript | core |
| `hello.py` | Minimal text (`tft_config`) | CPython · MCU · Wokwi | core |
| `color_test.py` | Color bars | CPython · MCU | core |
| `logo.py` | Logo drawing | CPython · MCU | core |
| `displaysys_simpletest.py` | Display smoke test | CPython · MCU | core |
| `displaysys_block_test.py` | Block transfer test | CPython · MCU | core |
| `displaysys_fill_rect_test.py` | Fill rect test | CPython · MCU | core |

## Events and input

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `eventsys_simpletest.py` | Event loop basics | CPython · MCU · PyScript | core |
| `eventsys_touch_test.py` | Touch events | CPython · MCU | core |
| `eventsys_encoder_test.py` | Rotary encoder | MCU | core |
| `scroll_touch_test.py` | Touch scrolling | CPython · MCU | core |
| `scroll_touch_test_displaybuf.py` | Scroll with DisplayBuffer | MCU | add_ons |
| `joystick_list_select.py` | Joystick + list | CPython · MCU | core |
| `keypins_simpletest.py` | Keypad pins | MCU | add_ons |

## Drawing and fonts

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `framebuf_simpletest.py` | framebuf API | CPython · MCU | core |
| `graphics_simpletest.py` | graphics module | CPython · MCU | core |
| `graphics_area_test.py` | Area bounding boxes | CPython · MCU | core |
| `font_simpletest.py` | Font: string FB + one `blit_rect` (opaque bg) | CPython · MCU | core |
| `font_simpletest2.py` | Font: direct on `display_drv` (transparent, per-pixel) | CPython · MCU | core |
| `font_simpletest3.py` | Font: `DisplayBuffer` + dirty blit (transparent, lowest bus cost) | CPython · MCU | core |
| `font_list.py` | List / preview `.bin` fonts from a directory | CPython · MCU | core |
| `fonts.py` | Page through fonts | CPython · MCU | core |
| `boxlines.py` | Lines and boxes | CPython · MCU | core |
| `bouncing_balls.py` | Colored balls animation | CPython · MCU · PyScript | core |

## Bitmaps and palettes

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `bmp565_simpletest.py` | BMP565 load/draw | CPython · MCU | graphics |
| `bmp565_blit.py` | Blit operations | CPython · MCU | graphics |
| `bmp565_sprite.py` | Sprite animation | CPython · MCU | graphics |
| `bmp565_sprite_transparent.py` | Transparency | CPython · MCU | graphics |
| `bmp565_scroll.py` | Scrolling bitmap | CPython · MCU | graphics |
| `bmp565_scroll_sprite.py` | Scrolling sprite | CPython · MCU | graphics |
| `palettes_material.py` | Material palette | CPython · MCU | add_ons |
| `palettes_wheel.py` | Color wheel | CPython · MCU | add_ons |
| `palettes_cube.py` | RGB cube | CPython · MCU | add_ons |
| `pbm_simpletest.py` | PBM images | CPython · MCU | add_ons |
| `png_test.py` | PNG (experimental) | CPython | add_ons |

## Widgets and apps

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `calculator.py` | Async calculator | CPython · PyScript | core |
| `paint.py` | Paint app | CPython · PyScript | core |
| `testris.py` | Tetris-like game | CPython · MCU | core |
| `apollo.py` | Apollo DSKY | CPython · PyScript | core |
| `widgets_*.py` | PyWidgets demos | CPython · MCU | add_ons |
| `console_simpletest.py` | Console add-on | CPython · MCU | add_ons |
| `console_advanced_demo.py` | Advanced console | CPython · MCU | add_ons |

## Display buffers and misc

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `displaybuf_simpletest.py` | DisplayBuffer | CPython · MCU | add_ons |
| `displaybuf_blit.py` | DisplayBuffer blit | MCU | add_ons |
| `scroll.py` | Scrolling text | CPython · MCU | core |
| `rotations.py` | Display rotation | CPython · MCU | core |
| `nano_gui_simpletest.py` | Nano-GUI hardware check | CPython · MCU | add_ons + upstream `gui/` |
| `lv_test_timer.py` | LVGL timer (follows `runtime.timer_async`) | CPython · MCU · PyScript | LVGL |

## Subdirectories

Runnable demos in subfolders may use the same `# pyscript gallery:` markers as top-level examples.

| Directory | Script | Platforms | Notes |
|-----------|--------|-----------|-------|
| `alien/` | `alien.py` | CPython · MP · MCU | Sprite bounce; `runtime.poll()` quit each frame |
| `chango/` | `chango.py` | CPython · MP · MCU · PyScript | One-shot font demo; `runtime.poll()` after draws |
| `noto_fonts/` | `noto_fonts.py` | MP · MCU · PyScript | One-shot Noto font demo; same tail as `chango` |
| `proverbs/` | `proverbs.py` | CPython · MP · MCU | Chinese proverb slideshow; quit via `runtime.poll()` |
| `tiny_toasters/` | `tiny_toasters.py` | CPython · MP · MCU | Sprite animation; quit via `runtime.poll()` |
| `apollo_dsky/` | — | — | Support module for top-level `apollo.py` |
| `assets/` | — | — | Shared fonts and images |

## Screenshots and live demos

See [Try pydisplay](../try/index.md) for the full gallery and browser/Wokwi demos.
