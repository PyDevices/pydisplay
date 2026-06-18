# LVGL

Use pydisplay as the display and input layer for [LVGL on MicroPython](https://github.com/lvgl/lv_micropython).

## Minimum install

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/displaysys.json")
mip.install("github:PyDevices/pydisplay/packages/eventsys.json")
mip.install("github:PyDevices/pydisplay/board_configs/<your_board>")
```

See the [minimum Wokwi project](https://wokwi.com/projects/404248867674669057).

## lv_config.py

LVGL needs a board-specific `lv_config.py` that connects LVGL's flush and input callbacks to displaysys. Create one following upstream LVGL micropython examples, using your `board_config.py` display and touch brokers.

There is no canonical `lv_config.py` in this repo yet — contributions welcome.

## Fast bus drivers

For performance on ESP32, consider [kdschlosser's lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython) C bus drivers with BusDisplay.

## Example

`src/examples/lv_touch_test.py` — LVGL touch test (requires LVGL firmware/build on device).
