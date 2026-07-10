# Examples catalog

All examples live in [`src/examples/`](https://github.com/PyDevices/pydisplay/tree/main/src/examples/).

```python
mip.install("github:PyDevices/pydisplay/packages/examples.json", target="./examples")
```

Use `import lib.path` first in a development clone (see [full clone](../installation/full-clone.md)).

!!! tip "Start here"
    New to pydisplay? Copy the [**App starter**](app-starter.md) boilerplate to begin your first app, then read the [**pydisplay_demo** guide](pydisplay_demo.md) for rotation, scrolling, and buffered text.

## multimer portability markers

As examples are reviewed for [multimer](../concepts/multimer.md) portability (sync, queued, and async timer patterns), each updated script gets a **first-line comment** tagging which timer styles it supports:

```python
# multimer types: all
```

Every runnable example (top-level scripts under `src/examples/*.py` and the subdirectory demos) carries a marker. Shared modules and test harnesses are tagged `NA`.

### Tag values

| Tag | Meaning |
|-----|---------|
| `all` | Same code on MCU, desktop sync, and PyScript/Jupyter blocking mode — poll/`sleep_ms` loops with quit handling, guarded `needs_pump()`/`pump()`, or library helpers (`pd.run_forever`) that hide pump details |
| `queued, sync` | Explicit `run_forever`/`periodic` timer loop or pump-centric game/LVGL test (`pydisplay_demo`, `testris`, `timer_simpletest`, `lv_test_timer_*`) |
| `sync` | Sync-only or one-shot on the main thread (`lv_test_timer_no_pump.py` hangs on pump backends; `console_advanced_demo.py` uses `os.dupterm` + one `display_drv.show()`) |
| `async` | `runtime.timer_async` + `asyncio` main loop |
| `NA` | Not applicable — shared module or test harness, not a runnable portability example (`lv_test_timer_common.py`, `lv_test_timer_harness.py`) |

### Search commands

List all marked examples:

```bash
rg '^# multimer types:' src/examples/*.py
```

List examples tagged for every timer style:

```bash
rg '^# multimer types: all' src/examples/*.py
```

List unmarked top-level examples:

```bash
comm -23 \
  <(ls -1 src/examples/*.py | xargs -I{} basename {} | sort) \
  <(rg -l '# multimer types:' src/examples/*.py | xargs -I{} basename {} | sort)
```

List all marked examples (recursive, including subdirectories):

```bash
rg '^# multimer types:' src/examples/
```

List unmarked runnable scripts (path-based; excludes support modules without markers by design):

```bash
comm -23 \
  <(find src/examples -path '*/.*' -prune -o -name '*.py' -print | sort) \
  <(rg -l '# multimer types:' src/examples/ -g '*.py' | sort)
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

**Finite queued/sync test** — [`timer_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/timer_simpletest.py):

```python
while not _done:
    pump()
    sleep_ms(1)
```

**Forever LVGL / library-driven app** — [`lv_touch_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_touch_test.py): setup UI, then drain the queue only when needed:

```python
from multimer import Timer, pump, sleep_ms

if getattr(Timer, "NEEDS_PUMP", False):
    while True:
        pump()
        sleep_ms(1)
```

On sync platforms the `if` block is skipped; on queued platforms (CPython SDL, CircuitPython threading) the loop keeps timer callbacks and display refresh alive.

**`tft_config` animation / one-shot** — subdirectory demos [`alien/alien.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/alien/alien.py), [`tiny_toasters/tiny_toasters.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tiny_toasters/tiny_toasters.py), [`chango/chango.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/chango/chango.py):

```python
from board_config import runtime
from multimer import Timer, needs_pump, pump

tft.show()
if needs_pump():
    pump()
if runtime is not None:
    runtime.poll()  # SDL message pump — required on MicroPython Windows
```

On **MicroPython Windows** (and other ports using `multimer._polling`), `multimer.needs_pump()` is false but `Timer.NEEDS_PUMP` is true — check the **timer class** flag when the module flag is false. Without `runtime.poll()`, the SDL window can freeze after the first frame even when the Python loop keeps running.

**LVGL apps** — [`lv_touch_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_touch_test.py):

```python
import display_driver

# ... build LVGL UI ...
display_driver.run()
```

`display_driver.run()` returns immediately on **MicroPython unix** and **CPython** (non-Windows) when `lv_utils` is already running — REPL stays usable. It blocks on **Windows** (`pump()` + `runtime.poll()`) and **macOS** (`lv_utils` tick loop). See [LVGL guide](../guis/lvgl.md).

**PyWidgets (pdwidgets)** — [`widgets_stub.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/widgets_stub.py): build UI, then:

```python
import pdwidgets as pd

pd.init_timer(10)  # optional; omit for poll mode
# ... widgets ...
pd.run_forever()
```

`run_forever()` drains `pump()` on queued backends; in poll mode it calls `pd.tick()`. On sync MCU with a timer, it returns immediately. On CPython Linux SDL it drives `tick()` from the main loop. See [PyWidgets](../guis/pywidgets.md#event-loop).

### Notes

- `displaysys_simpletest.py` handles `events.QUIT` in its poll loop (tagged `all`). Same quit pattern as [`scroll_touch_test_displaybuf.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/scroll_touch_test_displaybuf.py).
- `font_simpletest.py` — string-sized `FrameBuffer`, opaque background, one `blit_rect` per draw (see [Font rendering patterns](../concepts/graphics.md#choosing-a-font-rendering-pattern)).
- `font_simpletest2.py` — `Font.text(display_drv, …)`; transparent, per-pixel (slowest bus pattern).
- `font_simpletest3.py` — `DisplayBuffer` + `show(dirty)`; transparent, best when RAM allows a full-screen buffer.
- `nano_gui_simpletest.py` is tagged `all`; requires upstream [`gui/`](../guis/nano-gui.md) in `add_ons/`.
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
| `timer_simpletest.py` | multimer timer | CPython · MCU | core |
| `nano_gui_simpletest.py` | Nano-GUI hardware check | CPython · MCU | add_ons + upstream `gui/` |
| `lv_touch_test.py` | LVGL touch grid | MCU | LVGL |
| `lv_test_timer_no_pump.py` | LVGL timer — no pump loop | MCU · CPython Linux | LVGL |
| `lv_test_timer_pump.py` | LVGL timer — `pump()` drain loop | CPython · MCU | LVGL |
| `lv_test_timer_async.py` | LVGL timer — asyncio / PyScript | CPython · PyScript | LVGL |

## Subdirectories

Runnable demos in subfolders use the same multimer markers as top-level examples (`# multimer types: …` first line).

| Directory | Script | Tag | Platforms | Notes |
|-----------|--------|-----|-----------|-------|
| `alien/` | `alien.py` | `all` | CPython · MP · MCU | Sprite bounce; `needs_pump()` + `runtime.poll()` quit each frame |
| `chango/` | `chango.py` | `all` | CPython · MP · MCU · PyScript | One-shot font demo; `needs_pump()` + `runtime.poll()` after draws |
| `noto_fonts/` | `noto_fonts.py` | `all` | MP · MCU · PyScript | One-shot Noto font demo; same tail as `chango` |
| `proverbs/` | `proverbs.py` | `all` | CPython · MP · MCU | Chinese proverb slideshow; quit via `runtime.poll()` |
| `tiny_toasters/` | `tiny_toasters.py` | `all` | CPython · MP · MCU | Sprite animation; quit via `runtime.poll()` |
| `apollo_dsky/` | — | — | — | Support module for top-level `apollo.py` |
| `assets/` | — | — | — | Shared fonts and images |

## Screenshots and live demos

See [Try pydisplay](../try/index.md) for the full gallery and browser/Wokwi demos.
