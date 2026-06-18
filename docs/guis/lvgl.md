# LVGL

Use pydisplay as the display and input layer for [LVGL on MicroPython](https://github.com/lvgl/lv_micropython).

## Minimum install

```python
import mip
mip.install("github:PyDevices/pydisplay/packages/displaysys.json")
mip.install("github:PyDevices/pydisplay/packages/eventsys.json")
mip.install("github:PyDevices/pydisplay/board_configs/<your_board>")
```

See the [minimum Wokwi project](https://wokwi.com/projects/404248867674669057) for a working displaysys + eventsys + board config setup.

## Integration

Follow upstream [lv_micropython](https://github.com/lvgl/lv_micropython) documentation to connect LVGL's display flush and input callbacks to your pydisplay `board_config.py` display and touch brokers.

For faster ESP32 buses, consider [kdschlosser's lvgl_micropython](https://github.com/kdschlosser/lvgl_micropython) C drivers with BusDisplay.

## Example

`src/examples/lv_touch_test.py` — LVGL touch test (requires LVGL firmware/build on device).

## Helper

`src/add_ons/lv_utils.py` and `src/add_ons/lv_timer.py` — optional utilities when integrating LVGL with pydisplay.
