"""
lv_test_timer_common.py

Shared LVGL UI for lv_test_timer_sync, lv_test_timer_async, and
lv_test_timer_queued.  Not intended to be run directly.
"""

import lvgl as lv

_seconds = 0
_taps = 0
_arc_angle = 0


def get_state():
    """Return timer test counters for automated harness checks."""
    return {"seconds": _seconds, "taps": _taps}


def reset_taps():
    """Reset tap counter between harness sub-tests."""
    global _taps
    _taps = 0


def build_ui():
    """Build the timer test screen: title, seconds counter, arc, tap button.

    Returns:
        lv.button: The tap button (for harness coordinate / event injection).
    """
    scr = lv.screen_active()

    title = lv.label(scr)
    title.set_text("LVGL Timer Test")
    title.align(lv.ALIGN.TOP_MID, 0, 10)

    seconds_lbl = lv.label(scr)
    seconds_lbl.set_text("Seconds: 0")
    seconds_lbl.align(lv.ALIGN.CENTER, 0, -30)

    arc = lv.arc(scr)
    arc.set_size(80, 80)
    arc.align(lv.ALIGN.CENTER, 0, 30)
    arc.set_bg_angles(0, 360)
    arc.set_angles(0, 0)
    arc.remove_style(None, lv.PART.KNOB)
    try:
        arc.remove_flag(lv.obj.FLAG.CLICKABLE)
    except AttributeError:
        try:
            arc.clear_flag(lv.obj.FLAG.CLICKABLE)
        except AttributeError:
            pass

    btn = lv.button(scr)
    btn.set_size(120, 50)
    btn.align(lv.ALIGN.BOTTOM_MID, 0, -30)
    btn_lbl = lv.label(btn)
    btn_lbl.set_text("Tap me (0)")
    btn_lbl.center()

    def on_seconds_timer(_t):
        global _seconds
        _seconds += 1
        seconds_lbl.set_text(f"Seconds: {_seconds}")

    def on_arc_timer(_t):
        global _arc_angle
        _arc_angle = (_arc_angle + 10) % 360
        arc.set_angles(0, _arc_angle)

    def on_click(_e):
        global _taps
        _taps += 1
        btn_lbl.set_text(f"Tap me ({_taps})")

    lv.timer_create(on_seconds_timer, 1000, None)
    lv.timer_create(on_arc_timer, 50, None)
    btn.add_event_cb(on_click, lv.EVENT.CLICKED, None)
    return btn
