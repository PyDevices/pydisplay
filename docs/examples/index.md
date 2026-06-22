# Examples catalog

All examples live in [`src/examples/`](https://github.com/PyDevices/pydisplay/tree/main/src/examples/).

```python
mip.install("github:PyDevices/pydisplay/packages/examples.json", target="./examples")
```

Use `import lib.path` first in a development clone (see [full clone](../installation/full-clone.md)).

## multimer portability markers

As examples are reviewed for [multimer](../concepts/multimer.md) portability (sync, queued, and async timer patterns), each updated script gets a **first-line comment** tagging which timer styles it supports:

```python
# multimer types: all
```

**Progress (top-level `src/examples/*.py`):** **60 / 62** marked · **1** unmarked (`png_test.py`).

### Tag values

| Tag | Meaning |
|-----|---------|
| `all` | Works on sync, queued, and async timer backends without code changes (often one-shot + `display_drv.show()`, or event-poll + `show()`) |
| `queued, sync` | Blocking loop with `run_queued()` + `sleep_ms()` (or finite variant in `timer_simpletest.py`) |
| `sync` | Sync-only or one-shot on the main thread (`lv_test_timer_sync.py` exits on queued platforms; `console_advanced_demo.py` uses `os.dupterm` + one `display_drv.show()`) |
| `async` | `TIMER_ASYNC` + `asyncio` main loop |
| `untested` | Marked for catalog coverage; multimer portability not yet tested (`widgets_*.py`, `joystick_list_select.py`) |
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

List unmarked examples:

```bash
comm -23 \
  <(ls -1 src/examples/*.py | xargs -I{} basename {} | sort) \
  <(rg -l '# multimer types:' src/examples/*.py | xargs -I{} basename {} | sort)
```

### Canonical patterns

**Event-driven poll** — [`displaysys_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/displaysys_simpletest.py), [`eventsys_encoder_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/eventsys_encoder_test.py):

```python
display_drv.show()  # after initial draw
while True:
    if elist := broker.poll():
        for e in elist:
            ...  # draw on event
            display_drv.show()
```

**Finite queued/sync test** — [`timer_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/timer_simpletest.py):

```python
while not _done:
    run_queued()
    sleep_ms(1)
```

**Forever LVGL / library-driven app** — [`lv_touch_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_touch_test.py): setup UI, then drain the queue only when needed:

```python
from multimer import Timer
if getattr(Timer, "REQUIRES_RUN_QUEUED", False):
    from multimer import run_queued, sleep_ms
    while True:
        run_queued()
        sleep_ms(1)
```

On sync platforms the `if` block is skipped; on queued platforms (CPython SDL, CircuitPython threading) the loop keeps timer callbacks and display refresh alive.

### Notes

- `displaysys_simpletest.py` and `eventsys_encoder_test.py` are tagged `all` but use event loops: call `display_drv.show()` after draws (no `run_queued()`). Same pattern as [`scroll_touch_test_displaybuf.py`](scroll_touch_test_displaybuf.py).
- `font_simpletest.py` is tagged `all` but the framebuffer `blit_rect` path is blank on CircuitPython and MicroPython Windows; `font_simpletest2.py` (direct draw) works on tested platforms.
- `nano_gui_simpletest.py` is tagged `all`; requires upstream [`gui/`](../guis/nano-gui.md) in `add_ons/`.
**Legend:** Platforms = CPython · MCU · PyScript · Wokwi · Packages = core · add_ons · LVGL

## Suggested learning order

| Step | Script | Platforms | Packages | Screenshot |
|------|--------|-----------|----------|------------|
| 1 | `hello.py` | CPython · MCU · Wokwi | core | — |
| 2 | `color_test.py` | CPython · MCU | core | [color_test](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/color_test.png) |
| 3 | `displaysys_simpletest.py` | CPython · MCU | core | — |
| 4 | `eventsys_simpletest.py` | CPython · MCU · PyScript | core | — |
| 5 | `framebuf_simpletest.py` | CPython · MCU | core | [framebuf](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/framebuf_simpletest.png) |
| 6 | `graphics_simpletest.py` | CPython · MCU | core | [shapes](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/shapes_simpletest.png) |
| 7 | `eventsys_touch_test.py` | CPython · MCU | core | — |
| 8 | `calculator.py` | CPython · PyScript | core | [calculator](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/calculator.png) |
| 9 | `paint.py` | CPython · PyScript | core | [paint](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/paint.png) |
| 10 | `widgets_simpletest.py` | CPython · MCU | add_ons | — |

PyScript requires asyncio — see [PyScript asyncio guide](../guides/pyscript-asyncio.md).

## Hello and basics

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `hello.py` | Minimal text | CPython · MCU · Wokwi | core |
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
| `font_simpletest.py` | Font rendering | CPython · MCU | core |
| `font_simpletest2.py`, `font_simpletest3.py` | More fonts | CPython · MCU | core |
| `font_list.py` | Font picker | CPython · MCU | core |
| `fonts.py` | Page through fonts | CPython · MCU | core |
| `boxlines.py` | Lines and boxes | CPython · MCU | core |

## Bitmaps and palettes

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `bmp565_simpletest.py` | BMP565 load/draw | CPython · MCU | add_ons |
| `bmp565_blit.py` | Blit operations | CPython · MCU | add_ons |
| `bmp565_sprite.py` | Sprite animation | CPython · MCU | add_ons |
| `bmp565_sprite_transparent.py` | Transparency | CPython · MCU | add_ons |
| `bmp565_scroll.py` | Scrolling bitmap | CPython · MCU | add_ons |
| `bmp565_scroll_sprite.py` | Scrolling sprite | CPython · MCU | add_ons |
| `palettes_material.py` | Material palette | CPython · MCU | core |
| `palettes_wheel.py` | Color wheel | CPython · MCU | core |
| `palettes_cube.py` | RGB cube | CPython · MCU | core |
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
| `lv_test_timer_sync.py` | LVGL timer — sync (no loop) | MCU · CPython Linux | LVGL |
| `lv_test_timer_queued.py` | LVGL timer — sync + `run_queued()` | CPython · MCU | LVGL |
| `lv_test_timer_async.py` | LVGL timer — asyncio / PyScript | CPython · PyScript | LVGL |

## Subdirectories

| Directory | Content | Screenshot |
|-----------|---------|------------|
| `alien/` | Sprite demo | — |
| `apollo_dsky/` | Apollo assets | — |
| `assets/` | Shared fonts and images | — |
| `chango/` | Chango font demos | [chango](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/chango.png) |
| `noto_fonts/` | Noto font examples | [noto](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/noto_fonts.png) |
| `proverbs/` | Scrolling proverbs | [proverbs](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/proverbs.png) |
| `tiny_toasters/` | Tiny Toasters game | [tiny_toasters](https://raw.githubusercontent.com/PyDevices/pydisplay/main/screenshots/tiny_toasters.gif) |

## Screenshots and live demos

See [Try pydisplay](../try/index.md) for the full gallery and browser/Wokwi demos.
