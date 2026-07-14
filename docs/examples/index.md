# 🎨 Examples catalog

All examples live in [`src/examples/`](https://github.com/PyDevices/pydisplay/tree/main/src/examples/).

```python
mip.install("github:PyDevices/pydisplay/packages/examples.json", target="./examples")
```

Use `import lib.path` first in a development clone (see [full clone](../installation/full-clone.md)).

!!! tip "Start here"
    New to pydisplay? Copy the [**App starter**](app-starter.md) boilerplate to begin your first app, then read the [**pydisplay_demo** guide](pydisplay_demo.md) for rotation, scrolling, and buffered text.

## PyScript gallery markers

Every example **entry point** under `src/examples/` is included in the
[browser gallery](https://PyDevices.github.io/pydisplay/pyscript/) by default
(`scripts/pyscript_gen_packages.py`):

| Entry | Kind |
|-------|------|
| `examples/<name>.py` | module (`?modules=`) |
| `examples/<name>/<name>.py` | package manifest (`?manifests=`) |
| `examples/<name>/__init__.py` | package manifest (if no `<name>.py`) |

Optional header comments (first 10 lines):

```python
# pyscript skip: gallery
# pyscript featured
# pyscript modules: calc_engine
# pyscript packages: micropython-nano-gui
```

| Marker | Effect |
|--------|--------|
| `# pyscript skip: gallery` | Omit from the card grid |
| `# pyscript featured` | Pin to the top of the gallery (badge) |
| `# pyscript modules: …` | Extra same-tree modules to mip-install with the entry |
| `# pyscript packages: …` | Repo-root mip packages (e.g. Hinch `gui/`) pre-installed into `/add_ons` before import |

See [PyScript local development](../guides/pyscript.md).

### Search commands

```bash
rg '^# pyscript skip:' src/examples/
rg '^# pyscript featured' src/examples/
rg '^# pyscript modules:' src/examples/
rg '^# pyscript packages:' src/examples/
```

### Canonical patterns

**`runtime.run_forever()` with callbacks** — [`hello.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/hello.py), [`scroll.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/scroll.py), [`pydisplay_demo.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/pydisplay_demo.py), [`calc_graphics.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/calc_graphics.py):

```python
from board_config import display_drv, runtime

def on_click(e):
    ...

runtime.on(runtime.events.MOUSEBUTTONDOWN, on_click)
runtime.run_forever()
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

**Forever LVGL / library-driven app** — [`lv_test_timer.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer.py): build UI then `runtime.run_forever()`. Kit mode keeps a small sync/async wait for LVGL click injection.

**`tft_config` animation / one-shot** — subdirectory demos [`alien/alien.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/alien/alien.py), [`tiny_toasters/tiny_toasters.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/tiny_toasters/tiny_toasters.py), [`chango/chango.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/chango/chango.py):

```python
from board_config import runtime

tft.show()
runtime.run_forever()
```

**LVGL apps** — [`lv_test_timer.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/lv_test_timer.py): import `display_driver`, build UI, then `runtime.run_forever()`. See [LVGL guide](../guis/lvgl.md).

**PyWidgets (pdwidgets)** — [`widgets_percent.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/widgets_percent.py): build UI, then:

```python
import pdwidgets as pd

pd.init_timer(10)  # optional; sets poll delay for run_forever
# ... widgets ...
pd.run_forever()
```

`run_forever()` calls `pd.tick()` each frame then polls the runtime. During setup bursts before `run_forever()`, call `pd.tick()` to flush draws. See [PyWidgets](../guis/pywidgets.md#event-loop).

### Notes

- `font_simpletest.py` — cycles `string_blit` → `per_pixel` → `displaybuf` in one run (see [Font rendering patterns](../concepts/graphics.md#choosing-a-font-rendering-pattern)).
- `nano_gui_simpletest.py` / `micro_gui_simpletest.py` / `touch_gui_simpletest.py` need the matching Peter Hinch `gui/` in `add_ons/` (via `fetch_ph_gui` / mip).
**Legend:** Platforms = CPython · MCU · PyScript · Wokwi · Packages = core · add_ons · LVGL

## Suggested learning order

| Step | Script | Platforms | Packages | Screenshot |
|------|--------|-----------|----------|------------|
| 0 | [**App starter**](app-starter.md) (doc boilerplate) | CPython · MCU · PyScript | core | — |
| 1 | [`pydisplay_demo.py`](pydisplay_demo.md) | CPython · MCU | core | — |
| 2 | `color_test.py` | CPython · MCU | core | [color_test](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/color_test.png) |
| 3 | `eventsys_simpletest.py` | CPython · MCU · PyScript | core | — |
| 4 | `framebuf_simpletest.py` | CPython · MCU | core | [framebuf](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/framebuf_simpletest.png) |
| 5 | `graphics_simpletest.py` | CPython · MCU | core | [shapes](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/shapes_simpletest.png) |
| 6 | `eventsys_touch_test.py` | CPython · MCU | core | — |
| 7 | `calc_graphics.py` | CPython · PyScript | core | — |
| 8 | `paint.py` | CPython · PyScript | core | [paint](https://raw.githubusercontent.com/PyDevices/pydisplay/main/assets/screenshots/paint.png) |
| 9 | `widgets_simpletest.py` | CPython · MCU | add_ons | — |

PyScript requires asyncio — see [PyScript asyncio guide](../guides/pyscript-asyncio.md).

## Hello and basics

| Resource | Description | Platforms | Packages |
|----------|-------------|-----------|----------|
| [**App starter**](app-starter.md) | Copy-paste app boilerplate (doc only) | CPython · MCU · PyScript | core |
| [`pydisplay_demo.py`](pydisplay_demo.md) | Clicks, rotation, scroll (`runtime.run_forever`) | CPython · MCU · PyScript | core |
| `hello.py` | Minimal text (`tft_config`) | CPython · MCU · Wokwi | core |
| `color_test.py` | Color bars | CPython · MCU | core |
| `logo.py` | Logo drawing | CPython · MCU | core |
| `displaysys_block_test.py` | Block transfer test | CPython · MCU | core |
| `displaysys_fill_rect_test.py` | Fill rect test | CPython · MCU | core |

## Events and input

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `eventsys_simpletest.py` | Event loop basics | CPython · MCU · PyScript | core |
| `eventsys_touch_test.py` | Touch events | CPython · MCU | core |
| `eventsys_encoder_test.py` | Rotary encoder | MCU | core |
| `scroll_touch_test.py` | Touch scrolling (cycles `display_drv` ↔ DisplayBuffer) | CPython · MCU | add_ons |
| `joystick_list_select.py` | Joystick + list | CPython · MCU | core |
| `keypins_simpletest.py` | Keypad pins | MCU | add_ons |

## Drawing and fonts

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `framebuf_simpletest.py` | framebuf API | CPython · MCU | core |
| `graphics_simpletest.py` | graphics module | CPython · MCU | core |
| `font_simpletest.py` | Font: cycles `string_blit` / `per_pixel` / `displaybuf` | CPython · MCU | add_ons |
| `font_list.py` | List / preview `.bin` fonts from a directory | CPython · MCU | core |
| `fonts.py` | Page through fonts | CPython · MCU | core |
| `boxlines.py` | Lines and boxes | CPython · MCU | core |
| `bouncing_balls.py` | Colored balls animation | CPython · MCU · PyScript | core |

## Bitmaps and palettes

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `bmp565_simpletest.py` | BMP565 load/draw (slice + full blit) | CPython · MCU | graphics |
| `bmp565_sprite.py` | Sprite animation | CPython · MCU | graphics |
| `bmp565_sprite_transparent.py` | Transparency | CPython · MCU | graphics |
| `bmp565_scroll.py` | Scrolling bitmap | CPython · MCU | graphics |
| `bmp565_scroll_sprite.py` | Scrolling sprite | CPython · MCU | graphics |
| `palettes_demo.py` | Palettes: cycles `wheel` / `cube` / `material` | CPython · MCU | core |
| `pbm_simpletest.py` | PBM images | CPython · MCU | core |

## Widgets and apps

| Script | Description | Platforms | Packages |
|--------|-------------|-----------|----------|
| `calc_graphics.py` | Pocket calculator (graphics) | CPython · MCU · PyScript | core |
| `calc_widgets.py` | Pocket calculator (pdwidgets) | CPython · MCU · PyScript | add_ons |
| `calc_lvgl.py` | Pocket calculator (LVGL) | CPython · MCU · PyScript | LVGL |
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
| `scroll.py` | Scrolling text | CPython · MCU | core |
| `rotations.py` | Display rotation | CPython · MCU | core |
| `nano_gui_simpletest.py` | Nano-GUI hardware check | CPython · MCU · PyScript | add_ons + `micropython-nano-gui` |
| `micro_gui_simpletest.py` | Micro-GUI smoke | CPython · MCU · PyScript | add_ons + `micropython-micro-gui` |
| `touch_gui_simpletest.py` | Touch GUI smoke | CPython · MCU · PyScript | add_ons + `micropython-touch` |
| `lv_test_timer.py` | LVGL timer (follows `runtime.timer_async`) | CPython · MCU · PyScript | LVGL |

## Subdirectories

Runnable demos in subfolders use the same entry rules (`<name>/<name>.py` or `__init__.py`) and optional `# pyscript skip:` / `featured` / `modules:` headers.

| Directory | Script | Platforms | Notes |
|-----------|--------|-----------|-------|
| `alien/` | `alien.py` | CPython · MP · MCU | Sprite bounce; `runtime.poll()` quit each frame |
| `chango/` | `chango.py` | CPython · MP · MCU · PyScript | One-shot font demo; `runtime.poll()` after draws |
| `noto_fonts/` | `noto_fonts.py` | MP · MCU · PyScript | One-shot Noto font demo; same tail as `chango` |
| `proverbs/` | `proverbs.py` | CPython · MP · MCU | Chinese proverb slideshow; quit via `runtime.poll()` |
| `tiny_toasters/` | `tiny_toasters.py` | CPython · MP · MCU | Sprite animation; quit via `runtime.poll()` |
| `apollo/` | `apollo.py` | CPython · PyScript | DSKY emulator (`dsky.py` + BMP assets) |
| `assets/` | — | — | Shared fonts and images |

## Screenshots and live demos

See [Try pydisplay](../try/index.md) for the full gallery and browser/Wokwi demos.
