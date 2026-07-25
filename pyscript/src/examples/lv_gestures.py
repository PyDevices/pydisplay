# deps: lvgl
"""
lv_gestures.py

LVGL multi-touch gesture smoke example (pinch scale).

* Single-touch (mouse / CST8xx-class): drag/tap still work; pinch inactive.
* Multi-touch (GT911 / real SDL fingers): pinch scales the box via
  ``LV_EVENT_GESTURE`` + ``event_get_pinch_scale``.

Requires LVGL built with ``LV_USE_FLOAT`` + ``LV_USE_GESTURE_RECOGNITION``
(feature-detected; falls back to a single-touch label if missing).
"""

import sys

_file = __file__.replace("\\", "/").split("/")
if len(_file) >= 2 and _file[-2] == "examples":
    _src = "/".join(_file[:-2]) or "."
else:
    _src = "."
if _src not in sys.path:
    sys.path.insert(0, _src)

import lib.path  # noqa: F401 — must be first

from board_config import display_drv, runtime

if runtime is not None and "display_driver" not in sys.modules:
    runtime.stop_timer()

import lvgl as lv

# Struct present when LV_USE_GESTURE_RECOGNITION is on (all ports).
_GESTURE_OK = hasattr(lv, "indev_touch_data_t") and hasattr(lv, "INDEV_GESTURE")


def _event_gesture_type(e):
    fn = getattr(lv, "event_get_gesture_type", None)
    if fn is not None:
        return fn(e)
    return e.get_gesture_type()


def _event_pinch_scale(e):
    fn = getattr(lv, "event_get_pinch_scale", None)
    if fn is not None:
        return fn(e)
    return e.get_pinch_scale()


def build_ui():
    import display_driver

    inst = display_driver.event_loop.current_instance()
    if inst is not None:
        inst.disable()
    try:
        scr = lv.screen_active()
        scr.set_style_bg_color(lv.color_hex(0x202020), 0)

        title = lv.label(scr)
        title.set_text("LVGL gestures")
        title.align(lv.ALIGN.TOP_MID, 0, 8)

        status = lv.label(scr)
        if _GESTURE_OK:
            status.set_text("Pinch with 2 fingers (or tap with 1)")
        else:
            status.set_text("Gesture APIs unavailable (float/gesture off)")
        status.align(lv.ALIGN.TOP_MID, 0, 28)

        scale_lbl = lv.label(scr)
        scale_lbl.set_text("scale: 1.00")
        scale_lbl.align(lv.ALIGN.TOP_MID, 0, 48)

        box = lv.obj(scr)
        box.set_size(120, 120)
        box.center()
        box.set_style_bg_color(lv.color_hex(0x4080FF), 0)
        box.set_style_radius(12, 0)

        base_w = 120
        base_h = 120
        state = {"scale": 1.0}

        def _on_gesture(e):
            if not _GESTURE_OK:
                return
            try:
                gtype = _event_gesture_type(e)
            except Exception:
                return
            if gtype != lv.INDEV_GESTURE.PINCH:
                return
            try:
                scale = float(_event_pinch_scale(e))
            except Exception:
                return
            if scale <= 0:
                return
            state["scale"] = scale
            w = max(40, min(280, int(base_w * scale)))
            h = max(40, min(280, int(base_h * scale)))
            box.set_size(w, h)
            box.center()
            scale_lbl.set_text("scale: {:.2f}".format(scale))

        if _GESTURE_OK:
            scr.add_event_cb(_on_gesture, lv.EVENT.GESTURE, None)

        btn = lv.button(scr)
        btn.set_size(100, 40)
        btn.align(lv.ALIGN.BOTTOM_MID, 0, -12)
        bl = lv.label(btn)
        bl.set_text("Tap")
        bl.center()

        taps = {"n": 0}

        def _on_click(_e):
            taps["n"] += 1
            bl.set_text("Tap {}".format(taps["n"]))

        btn.add_event_cb(_on_click, lv.EVENT.CLICKED, None)
        return box, scale_lbl, taps
    finally:
        if inst is not None:
            inst.enable()


def main():
    build_ui()
    if runtime is not None:
        runtime.run_forever()


if __name__ == "__main__":
    main()
