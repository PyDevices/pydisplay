# multimer types: NA
"""
lv_test_timer_common.py

Shared LVGL UI for lv_test_timer_sync, lv_test_timer_async, and
lv_test_timer_queued.  Not intended to be run directly.
"""

import sys

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


def _format_timer_type(timer_cls):
    """Short label from a Timer class (multimer backend, machine, aio, …)."""
    if timer_cls is None:
        return "?"
    mod = getattr(timer_cls, "__module__", "?")
    name = getattr(timer_cls, "__name__", "?")
    part = mod.rsplit(".", 1)[-1]
    if part == "aio":
        return "aio"
    if part.startswith("_"):
        return part
    if mod in ("machine", "multimer"):
        return name if mod == "multimer" else mod
    return part if part == name else f"{part}.{name}"


def _runtime_label():
    impl = getattr(sys, "implementation", None)
    if impl is None:
        return "python"
    name = getattr(impl, "name", "python")
    ver = getattr(impl, "version", None)
    if ver and isinstance(ver, (tuple, list)) and ver:
        if len(ver) >= 2:
            return f"{name} {ver[0]}.{ver[1]}"
        return f"{name} {ver[0]}"
    return name


def _os_label():
    return sys.platform


def _lvgl_label():
    try:
        major = lv.version_major()
        minor = lv.version_minor()
        return f"{major}.{minor}"
    except AttributeError:
        pass
    try:
        info = lv.version_info()
        if info and len(info) >= 2:
            return f"{info[0]}.{info[1]}"
    except (AttributeError, TypeError):
        pass
    return "?"


def _display_type():
    try:
        from board_config import display_drv

        return type(display_drv).__name__
    except (ImportError, AttributeError):
        return "?"


def _timer_class():
    try:
        import board_config

        if getattr(board_config, "TIMER_ASYNC", False):
            from multimer.aio import Timer

            return Timer
    except ImportError:
        pass
    try:
        from multimer import Timer

        return Timer
    except ImportError:
        return None


def _timer_type():
    try:
        import lv_utils

        inst = lv_utils.event_loop.current_instance()
        if inst is not None:
            if inst.asynchronous and getattr(inst, "_aio_timer", None) is not None:
                return _format_timer_type(type(inst._aio_timer))
            timer = getattr(inst, "timer", None)
            if timer is not None and timer is not False:
                return _format_timer_type(type(timer))
    except ImportError:
        pass
    return _format_timer_type(_timer_class())


def get_platform_info():
    """Autodetected runtime, OS, display, timer, and LVGL labels for UI / harness."""
    return {
        "runtime": _runtime_label(),
        "os": _os_label(),
        "display": _display_type(),
        "timer": _timer_type(),
        "lvgl": _lvgl_label(),
    }


def timer_backend_name():
    """Short timer backend name (same value shown in the UI timer label)."""
    return get_platform_info()["timer"]


def _add_info_labels(scr, info, y_start=26, line_h=16):
    lines = (
        f"Runtime: {info['runtime']}",
        f"OS: {info['os']}",
        f"Display: {info['display']}",
        f"Timer: {info['timer']}",
        f"LVGL: {info['lvgl']}",
    )
    y = y_start
    for text in lines:
        lbl = lv.label(scr)
        lbl.set_text(text)
        lbl.align(lv.ALIGN.TOP_MID, 0, y)
        y += line_h


def build_ui():
    """Build the timer test screen: title, seconds counter, arc, tap button.

    Returns:
        lv.button: The tap button (for harness coordinate / event injection).
    """
    scr = lv.screen_active()
    info = get_platform_info()

    title = lv.label(scr)
    title.set_text("LVGL Timer Test")
    title.align(lv.ALIGN.TOP_MID, 0, 8)

    _add_info_labels(scr, info)

    seconds_lbl = lv.label(scr)
    seconds_lbl.set_text("Seconds: 0")
    seconds_lbl.align(lv.ALIGN.CENTER, 0, -48)

    arc = lv.arc(scr)
    arc.set_size(80, 80)
    arc.align(lv.ALIGN.CENTER, 0, 25)
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
