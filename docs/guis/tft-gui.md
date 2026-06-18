# TFT examples (russhughes)

Many pydisplay examples were ported from [@russhughes st7789py_mpy](https://github.com/russhughes/st7789py_mpy).

## Config

Use or adapt `tft_config.py` from [`src/add_ons/tft_config.py`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/tft_config.py). Some example filenames were search-replaced during port — if an example fails to import config, compare with that file.

## Font and image tools

- [text_font_converter.py](https://github.com/russhughes/st7789py_mpy/blob/master/utils/text_font_converter.py) → `tft_text.text()`
- [write_font_converter.py](https://github.com/russhughes/st7789py_mpy/blob/master/utils/write_font_converter.py) → `tft_write.write()`
- [image_converter.py](https://github.com/russhughes/st7789py_mpy/blob/master/utils/image_converter.py) → `.bitmap()`

See [Drawing and fonts](../concepts/drawing-and-fonts.md) and [Graphics files](../concepts/graphics-files.md).

## Notable examples

`tiny_hello.py`, `feathers.py`, `proverbs/`, `chango/`, `tiny_toasters/` (game port).
