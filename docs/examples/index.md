# Examples catalog

All examples live in [`src/examples/`](https://github.com/PyDevices/pydisplay/tree/main/src/examples/). Install via:

```python
mip.install("github:PyDevices/pydisplay/packages/examples.json", target="./examples")
```

Always run `import lib.path` first (development layout).

## Hello and basics

| Script | Description |
|--------|-------------|
| `hello.py` | Minimal text |
| `color_test.py` | Color bars |
| `logo.py` | Logo drawing |
| `displaysys_simpletest.py` | Display smoke test |
| `displaysys_block_test.py` | Block transfer test |
| `displaysys_fill_rect_test.py` | Fill rect test |

## Events and input

| Script | Description |
|--------|-------------|
| `eventsys_simpletest.py` | Event loop basics |
| `eventsys_touch_test.py` | Touch events |
| `eventsys_encoder_test.py` | Rotary encoder |
| `scroll_touch_test.py` | Touch scrolling |
| `scroll_touch_test_displaybuf.py` | Scroll with DisplayBuffer |
| `joystick_list_select.py` | Joystick + list |
| `keypins_simpletest.py` | Keypad pins |

## Drawing and fonts

| Script | Description |
|--------|-------------|
| `framebuf_simpletest.py` | framebuf API |
| `graphics_simpletest.py` | graphics module |
| `graphics_area_test.py` | Area bounding boxes |
| `font_simpletest.py` | Font rendering |
| `font_simpletest2.py`, `font_simpletest3.py` | More fonts |
| `font_list.py` | Font picker |
| `fonts.py` | Page through fonts |
| `ezfont_simpletest.py` | EZFont |
| `boxlines.py` | Lines and boxes |

## Bitmaps and palettes

| Script | Description |
|--------|-------------|
| `bmp565_simpletest.py` | BMP565 load/draw |
| `bmp565_blit.py` | Blit operations |
| `bmp565_sprite.py` | Sprite animation |
| `bmp565_sprite_transparent.py` | Transparency |
| `bmp565_scroll.py` | Scrolling bitmap |
| `bmp565_scroll_sprite.py` | Scrolling sprite |
| `palettes_material.py` | Material palette |
| `palettes_wheel.py` | Color wheel |
| `palettes_cube.py` | RGB cube |
| `pbm_simpletest.py` | PBM images |
| `png_test.py` | PNG (experimental) |

## Widgets and apps

| Script | Description |
|--------|-------------|
| `calculator.py` | Async calculator — **PyScript reference** |
| `paint.py` | Paint app |
| `testris.py` | Tetris-like game |
| `apollo.py` | Apollo DSKY |
| `widgets_*.py` | PyWidgets demos — see [PyWidgets](../guis/pywidgets.md) |
| `console_simpletest.py` | Console add-on |
| `console_advanced_demo.py` | Advanced console |

## Display buffers and misc

| Script | Description |
|--------|-------------|
| `displaybuf_simpletest.py` | DisplayBuffer |
| `displaybuf_blit.py` | DisplayBuffer blit |
| `scroll.py` | Scrolling text |
| `rotations.py` | Display rotation |
| `timer_simpletest.py` | multimer timer |
| `nano_gui_simpletest.py` | Nano-GUI |
| `lv_touch_test.py` | LVGL touch |

## Subdirectories

| Directory | Content |
|-----------|---------|
| `alien/` | Sprite demo |
| `apollo_dsky/` | Apollo assets |
| `assets/` | Shared fonts and images |
| `chango/` | Chango font demos |
| `noto_fonts/` | Noto font examples |
| `proverbs/` | Scrolling proverbs |
| `tiny_toasters/` | Tiny Toasters game |

## Screenshots

See [live demos](live-demos.md) for GIFs and stills of many examples.
