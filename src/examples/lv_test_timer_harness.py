# multimer types: NA
"""
lv_test_timer_harness.py

Automated LVGL timer + input test for ``sync`` and ``async`` modes.

The board's shared runtime timer drives LVGL (lv_utils subscribes its tick to it),
so there is no pump/no_pump distinction anymore: one ``sleep_ms(0)`` per loop
iteration is enough. This harness builds the shared UI, verifies LVGL timers
advance and that a simulated click reaches the LVGL button, then injects
``events.Quit`` and exits 0.

Prints a ``KIT_RESULT=`` JSON line on stdout before quit (tools/lv_timer_test_kit.py).
Uses only the public ``multimer`` API (``asyncio``, ``sleep_ms``).
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

_DURATION_S = 4
_RESULT_PREFIX = "KIT_RESULT="


def _timer_backend():
    try:
        from lv_test_timer_common import timer_backend_name

        return timer_backend_name()
    except Exception as exc:
        return f"error:{exc!r}"


def _button_center(btn):
    import lvgl as lv

    from board_config import height, width

    try:
        area = lv.area_t()
        btn.get_coords(area)
        return (area.x1 + area.x2) // 2, (area.y1 + area.y2) // 2
    except Exception:
        return width // 2, height - 55


class _FakeEvent:
    __slots__ = ("type", "button", "pos", "buttons")

    def __init__(self, etype, pos, button=1):
        self.type = etype
        self.button = button
        self.pos = pos
        self.buttons = (1, 0, 0)


def _pump_lvgl(n=15):
    import lvgl as lv

    for _ in range(n):
        if lv._nesting.value == 0:
            lv.task_handler()
        time.sleep(0.01)


def _inject_click(cx, cy):
    """Feed a press+release through the QUEUE device so LVGL's indev reads them.

    LVGL's pointer indev reads the virtual touch device from ``task_handler``
    (driven by the shared runtime timer), which pulls the mocked events out of the
    queue device — exactly like a real SDL mouse click. We only sleep here and
    let the timer's task_handler drain them (no main-thread LVGL calls, so no
    race with the timer-driven rendering).
    """
    import quit_inject
    from eventsys import events
    from lv_test_timer_common import get_state, reset_taps
    from multimer import sleep_ms

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
            sleep_ms(10)
    finally:
        queue_dev._read = orig_read
    return get_state()["taps"]


async def _inject_click_async(cx, cy):
    """Async click: yield to the loop so async_refresh runs task_handler."""
    import quit_inject
    from eventsys import events
    from lv_test_timer_common import get_state, reset_taps
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


def _emit_result(mode, state, taps):
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
        "backend": _timer_backend(),
        "seconds": seconds,
        "taps": taps,
    }
    print(_RESULT_PREFIX + json.dumps(payload, separators=(",", ":")))
    sys.stdout.flush()
    return payload


def _quit_and_exit(code=0):
    """Stop the shared timer, release the display, and hard-exit for the kit."""
    try:
        from board_config import runtime

        # Stop the timer first so no signal-driven rendering runs during teardown.
        runtime.stop_timer()
    except Exception:
        pass
    try:
        from board_config import display_drv

        display_drv.force_quit(code)
    except SystemExit:
        raise
    except Exception:
        pass
    raise SystemExit(code)


def _run_sync():
    import os

    os.environ["PYDISPLAY_TIMER_ASYNC"] = "0"
    import board_config  # noqa: F401

    import display_driver  # noqa: F401
    from lv_test_timer_common import build_ui, get_state
    from multimer import sleep_ms

    btn = build_ui("sync")

    # The runtime's timer drives LVGL (tick + task_handler + present) on its own;
    # the app loop just needs to sleep. Avoid touching LVGL/pygame on the main
    # thread here so we don't race the timer-driven rendering. Read the button
    # coords only once timers have advanced (LVGL has laid the UI out by then).
    deadline = time.time() + _DURATION_S
    clicked_taps = None
    while time.time() < deadline:
        sleep_ms(0)
        if clicked_taps is None and get_state()["seconds"] >= 2:
            cx, cy = _button_center(btn)
            clicked_taps = _inject_click(cx, cy)

    state = get_state()
    taps = clicked_taps if clicked_taps is not None else state["taps"]
    payload = _emit_result("sync", state, taps)
    _quit_and_exit(0 if payload["status"] == "ok" else 1)


def _run_async():
    import os

    os.environ["PYDISPLAY_TIMER_ASYNC"] = "1"
    import board_config  # noqa: F401

    from multimer import asyncio

    async def main():
        from board_config import runtime

        import display_driver  # noqa: F401
        from lv_test_timer_common import build_ui, get_state

        btn = build_ui("async")

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
        return _emit_result("async", state, taps)

    payload = asyncio.run(main())
    _quit_and_exit(0 if payload and payload.get("status") == "ok" else 1)


_MODES = {
    "sync": _run_sync,
    "async": _run_async,
}


def main(mode=None):
    mode = mode or (sys.argv[1] if len(sys.argv) > 1 else "sync")
    if mode not in _MODES:
        print(f"Unknown mode {mode!r}; use sync or async")
        raise SystemExit(2)
    try:
        _MODES[mode]()
    except SystemExit:
        raise
    except Exception as exc:
        _print = print
        _print(
            _RESULT_PREFIX
            + json.dumps(
                {"mode": mode, "status": "error", "backend": _timer_backend(), "error": repr(exc)},
                separators=(",", ":"),
            )
        )
        raise


if __name__ == "__main__":
    main()
