# pyscript gallery: async
"""
lv_test_timer.py

LVGL timer smoke test. Uses whatever timer mode ``board_config`` / ``runtime``
already has — does not read or write environment variables.

Shows runtime, OS, display, timer backend, and LVGL version; a seconds counter
and spinning arc prove LVGL timers fire; a tap button exercises input.

Matrix / interactive: ``dual_main`` follows ``runtime.timer_async``.
Automated kit: ``python examples/lv_test_timer.py kit`` (parent may set
``PYDISPLAY_TIMER_ASYNC`` before launch; this script still only follows runtime).
"""

import sys

_file = __file__.replace("\\", "/").split("/")
if len(_file) >= 2 and _file[-2] == "examples":
    _src = "/".join(_file[:-2]) or "."
else:
    _src = "."
if _src not in sys.path:
    sys.path.insert(0, _src)
_tools = _src + "/../tools"
if _tools not in sys.path:
    sys.path.insert(0, _tools)

import lib.path  # noqa: F401 — must be first

import json
import time

import lvgl as lv
from board_config import display_drv, runtime
from multimer.loop import dual_main

_seconds = 0
_taps = 0
_arc_angle = 0

_DURATION_S = 4
_RESULT_PREFIX = "KIT_RESULT="


def _mode_label():
    return "async" if getattr(runtime, "timer_async", False) else "sync"


def get_state():
    return {"seconds": _seconds, "taps": _taps}


def reset_taps():
    global _taps
    _taps = 0


def _format_timer_type(timer_cls):
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


def _lvgl_label():
    try:
        return f"{lv.version_major()}.{lv.version_minor()}"
    except AttributeError:
        pass
    try:
        info = lv.version_info()
        if info and len(info) >= 2:
            return f"{info[0]}.{info[1]}"
    except (AttributeError, TypeError):
        pass
    return "?"


def _timer_type():
    try:
        timer = getattr(runtime, "_timer", None)
        if timer is not None:
            return _format_timer_type(type(timer))
    except AttributeError:
        pass
    try:
        if getattr(runtime, "timer_async", False):
            from multimer import AsyncTimer as Timer
        else:
            from multimer import Timer
        return _format_timer_type(Timer)
    except ImportError:
        return "?"


def get_platform_info():
    return {
        "runtime": _runtime_label(),
        "os": sys.platform,
        "display": type(display_drv).__name__,
        "timer": _timer_type(),
        "lvgl": _lvgl_label(),
        "mode": _mode_label(),
    }


def timer_backend_name():
    return get_platform_info()["timer"]


def _add_info_labels(scr, info, y_start=26, line_h=16):
    lines = (
        f"Mode: {info['mode']}",
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
    """Build the timer test screen. Returns the tap button."""
    global _seconds, _taps, _arc_angle
    _seconds = 0
    _taps = 0
    _arc_angle = 0

    # Pause shared LVGL task_handler while constructing widgets (not re-entrant).
    inst = None
    try:
        import lv_utils

        inst = lv_utils.event_loop.current_instance()
    except ImportError:
        inst = None
    if inst is not None:
        inst.disable()
    try:
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
        arc.remove_flag(lv.obj.FLAG.CLICKABLE)

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
    finally:
        if inst is not None:
            inst.enable()


def _setup():
    """Import display_driver (LVGL) then build UI. Call from sync/async entry."""
    import display_driver  # noqa: F401

    return build_ui()


def _poll_done():
    if runtime.quit_requested:
        return True
    if getattr(display_drv, "_deinitialized", False):
        return True
    return False


def main_sync():
    _setup()
    # Avoid multimer.sleep_ms here: on CPython/Linux the librt signal handler
    # drives LVGL, and sleeping in the timer backend can deadlock the main thread.
    # Do not call runtime.poll() either while the signal-driven LVGL tick is live —
    # quit comes from the test-mode deadline hook (or window close via force_quit).
    from multimer import run_deadline_hook

    while True:
        run_deadline_hook()
        if _poll_done():
            break
        time.sleep(0.01)


async def main_async():
    _setup()
    from multimer import asyncio

    while True:
        runtime.poll()
        if _poll_done():
            break
        await asyncio.sleep(0)


# --- kit / automated path (tools/lv_timer_test_kit.py) ---


def _button_center(btn):
    from board_config import height, width

    try:
        area = lv.area_t()
        btn.get_coords(area)
        return (area.x1 + area.x2) // 2, (area.y1 + area.y2) // 2
    except Exception:
        return width // 2, height - 55


def _inject_click(cx, cy):
    import quit_inject
    from eventsys import events

    reset_taps()
    queue_dev = quit_inject.queue_device()
    if queue_dev is None:
        return 0

    pending = [
        events.Button(events.MOUSEBUTTONDOWN, (cx, cy), 1, False, None),
        events.Button(events.MOUSEBUTTONUP, (cx, cy), 1, False, None),
    ]
    orig_read = queue_dev._read

    def mock_read():
        return [pending.pop(0)] if pending else None

    queue_dev._read = mock_read
    try:
        deadline = time.time() + 1.5
        while (pending or get_state()["taps"] < 1) and time.time() < deadline:
            time.sleep(0.01)
    finally:
        queue_dev._read = orig_read
    return get_state()["taps"]


async def _inject_click_async(cx, cy):
    import quit_inject
    from eventsys import events
    from multimer import asyncio

    reset_taps()
    queue_dev = quit_inject.queue_device()
    if queue_dev is None:
        return 0

    pending = [
        events.Button(events.MOUSEBUTTONDOWN, (cx, cy), 1, False, None),
        events.Button(events.MOUSEBUTTONUP, (cx, cy), 1, False, None),
    ]
    orig_read = queue_dev._read

    def mock_read():
        return [pending.pop(0)] if pending else None

    queue_dev._read = mock_read
    try:
        deadline = time.time() + 1.5
        while (pending or get_state()["taps"] < 1) and time.time() < deadline:
            await asyncio.sleep(0.01)
    finally:
        queue_dev._read = orig_read
    return get_state()["taps"]


def _emit_result(state, taps):
    mode = _mode_label()
    seconds = state["seconds"]
    if seconds < 2:
        click, status = "no timers", "fail"
    elif taps >= 1:
        click, status = "ok", "ok"
    else:
        click, status = "no clicks", "fail"
    payload = {
        "mode": mode,
        "status": status,
        "click_status": click,
        "backend": timer_backend_name(),
        "seconds": seconds,
        "taps": taps,
    }
    print(_RESULT_PREFIX + json.dumps(payload, separators=(",", ":")))
    sys.stdout.flush()
    return payload


def _quit_and_exit(code=0):
    try:
        runtime.stop_timer()
    except Exception:
        pass
    try:
        display_drv.force_quit(code)
    except SystemExit:
        raise
    except Exception:
        pass
    raise SystemExit(code)


def _run_kit_sync():
    btn = _setup()
    deadline = time.time() + _DURATION_S
    clicked_taps = None
    while time.time() < deadline:
        # See main_sync: do not use multimer.sleep_ms with LVGL + librt.
        time.sleep(0.01)
        if clicked_taps is None and get_state()["seconds"] >= 2:
            cx, cy = _button_center(btn)
            clicked_taps = _inject_click(cx, cy)

    state = get_state()
    taps = clicked_taps if clicked_taps is not None else state["taps"]
    payload = _emit_result(state, taps)
    _quit_and_exit(0 if payload["status"] == "ok" else 1)


async def _run_kit_async():
    btn = _setup()
    from multimer import asyncio

    deadline = time.time() + _DURATION_S
    clicked_taps = None
    while time.time() < deadline:
        runtime.poll()
        await asyncio.sleep(0)
        if clicked_taps is None and get_state()["seconds"] >= 2:
            cx, cy = _button_center(btn)
            clicked_taps = await _inject_click_async(cx, cy)

    state = get_state()
    taps = clicked_taps if clicked_taps is not None else state["taps"]
    return _emit_result(state, taps)


def run_kit():
    """Automated timer + click check; follows ``runtime.timer_async``."""
    try:
        if runtime.timer_async:
            from multimer.loop import run

            payload = run(_run_kit_async)
            if payload is not None and hasattr(payload, "done"):
                _quit_and_exit(1)
            _quit_and_exit(0 if payload and payload.get("status") == "ok" else 1)
        else:
            _run_kit_sync()
    except SystemExit:
        raise
    except Exception as exc:
        print(
            _RESULT_PREFIX
            + json.dumps(
                {
                    "mode": _mode_label(),
                    "status": "error",
                    "backend": timer_backend_name(),
                    "error": repr(exc),
                },
                separators=(",", ":"),
            )
        )
        raise


def _wants_kit():
    return len(sys.argv) > 1 and sys.argv[1] in ("kit", "harness")


if _wants_kit():
    run_kit()
else:
    dual_main(main_sync, main_async, async_mode=runtime.timer_async)
