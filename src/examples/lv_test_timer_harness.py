# multimer types: NA
"""
lv_test_timer_harness.py

Automated LVGL timer + input test for sync, queued, and async modes.
After timer/click checks, injects ``events.Quit`` through the queue read path
and pumps LVGL (same path as clicking the window X) to verify clean shutdown.

Prints a KIT_RESULT= JSON line on stdout before quit; the process should exit
with code 0 (tools/lv_timer_test_kit.py).
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
import sys
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
    from board_config import height, width

    try:
        coords = btn.get_coords()
        if coords:
            x1, y1, x2, y2 = coords
            return (x1 + x2) // 2, (y1 + y2) // 2
    except Exception:
        pass
    return width // 2, height - 55


class _FakeEvent:
    __slots__ = ("type", "button", "pos", "buttons")

    def __init__(self, etype, pos, button=1):
        self.type = etype
        self.button = button
        self.pos = pos
        self.buttons = (1, 0, 0)


def _queue_device():
    import quit_inject

    return quit_inject.queue_device()


def _pump_lvgl(n=5, delay_s=0):
    import lvgl as lv

    for _ in range(n):
        if lv._nesting.value == 0:
            lv.task_handler()
        if delay_s:
            time.sleep(delay_s)


async def _pump_lvgl_async(n=5, delay_s=0):
    import lvgl as lv

    try:
        import asyncio
    except ImportError:
        import uasyncio as asyncio

    for _ in range(n):
        if lv._nesting.value == 0:
            lv.task_handler()
        if delay_s:
            await asyncio.sleep(delay_s)


def _test_sdl_click(cx, cy, *, broker_poll_first, pump=_pump_lvgl):
    """Simulate SDL mouse events via QueueDevice read; optional broker.poll steal."""
    from board_config import broker
    from eventsys import events
    from lv_test_timer_common import get_state, reset_taps

    reset_taps()
    queue_dev = _queue_device()
    if queue_dev is None:
        return {"skipped": True, "taps": 0}

    down = _FakeEvent(events.MOUSEBUTTONDOWN, (cx, cy))
    up = _FakeEvent(events.MOUSEBUTTONUP, (cx, cy))
    up.buttons = (0, 0, 0)
    pending = [down, up]

    def mock_read():
        if pending:
            return [pending.pop(0)]
        return None

    orig_read = queue_dev._read
    queue_dev._read = mock_read
    try:
        if broker_poll_first:
            broker.poll()
        pump(20, 0.02)
    finally:
        queue_dev._read = orig_read

    taps = get_state()["taps"]
    return {"taps": taps, "broker_poll_first": broker_poll_first}


def _inject_pointer_click(x, y, pump=_pump_lvgl):
    import lvgl as lv
    from eventsys import events
    from lv_test_timer_common import get_state, reset_taps

    reset_taps()
    down = _FakeEvent(events.MOUSEBUTTONDOWN, (x, y))
    up = _FakeEvent(events.MOUSEBUTTONUP, (x, y))

    queue_dev = _queue_device()
    if queue_dev is not None:
        vd = getattr(queue_dev, "_virtual_devices", None)
        if vd is not None:
            vd._vd_touch.add_event(down)
            pump(5, 0.02)
            vd._vd_touch.add_event(up)
            pump(15, 0.02)
            return get_state()["taps"]

    # Fallback: drive _touch_cb directly (MCU / no QUEUE device)
    import display_driver

    data = type("IndevData", (), {})()
    data.point = lv.point_t({"x": 0, "y": 0})
    data.state = lv.INDEV_STATE.RELEASED
    display_driver._touch_cb(down, None, data)
    pump(3)
    display_driver._touch_cb(up, None, data)
    pump(10)
    return get_state()["taps"]


def _emit_clicked(btn):
    import lvgl as lv

    try:
        lv.event_send(btn, lv.EVENT.CLICKED, btn)
    except Exception:
        return False
    lv.task_handler()
    return True


def _run_input_tests(btn, cx, cy, pump=_pump_lvgl):
    """Run SDL steal vs LV-only vs FIFO inject click diagnostics."""
    sdl_stolen = _test_sdl_click(cx, cy, broker_poll_first=True, pump=pump)
    sdl_lv_only = _test_sdl_click(cx, cy, broker_poll_first=False, pump=pump)
    fifo_taps = _inject_pointer_click(cx, cy, pump=pump)
    lv_ok = _emit_clicked(btn)
    from lv_test_timer_common import get_state

    return {
        "sdl_stolen_taps": sdl_stolen.get("taps", 0),
        "sdl_lv_taps": sdl_lv_only.get("taps", 0),
        "fifo_taps": fifo_taps,
        "lv_event_ok": lv_ok,
        "taps_total": get_state()["taps"],
    }


async def _run_input_tests_async(btn, cx, cy):
    """Async input diagnostics — must yield to the aio LVGL timer between pumps."""

    async def _test_async(cx, cy, *, broker_poll_first):
        from board_config import broker
        from eventsys import events
        from lv_test_timer_common import get_state, reset_taps

        reset_taps()
        queue_dev = _queue_device()
        if queue_dev is None:
            return {"taps": 0}
        down = _FakeEvent(events.MOUSEBUTTONDOWN, (cx, cy))
        up = _FakeEvent(events.MOUSEBUTTONUP, (cx, cy))
        up.buttons = (0, 0, 0)
        pending = [down, up]

        def mock_read():
            if pending:
                return [pending.pop(0)]
            return None

        orig_read = queue_dev._read
        queue_dev._read = mock_read
        try:
            if broker_poll_first:
                broker.poll()
            await _pump_lvgl_async(20, 0.02)
        finally:
            queue_dev._read = orig_read
        return {"taps": get_state()["taps"], "broker_poll_first": broker_poll_first}

    async def _inject_async(x, y):
        import lvgl as lv
        from eventsys import events
        from lv_test_timer_common import get_state, reset_taps

        reset_taps()
        down = _FakeEvent(events.MOUSEBUTTONDOWN, (x, y))
        up = _FakeEvent(events.MOUSEBUTTONUP, (x, y))
        queue_dev = _queue_device()
        if queue_dev is not None:
            vd = getattr(queue_dev, "_virtual_devices", None)
            if vd is not None:
                vd._vd_touch.add_event(down)
                await _pump_lvgl_async(5, 0.02)
                vd._vd_touch.add_event(up)
                await _pump_lvgl_async(15, 0.02)
                return get_state()["taps"]
        import display_driver

        data = type("IndevData", (), {})()
        data.point = lv.point_t({"x": 0, "y": 0})
        data.state = lv.INDEV_STATE.RELEASED
        display_driver._touch_cb(down, None, data)
        await _pump_lvgl_async(3)
        display_driver._touch_cb(up, None, data)
        await _pump_lvgl_async(10)
        return get_state()["taps"]

    sdl_stolen = await _test_async(cx, cy, broker_poll_first=True)
    sdl_lv_only = await _test_async(cx, cy, broker_poll_first=False)
    fifo_taps = await _inject_async(cx, cy)
    lv_ok = _emit_clicked(btn)
    from lv_test_timer_common import get_state

    return {
        "sdl_stolen_taps": sdl_stolen.get("taps", 0),
        "sdl_lv_taps": sdl_lv_only.get("taps", 0),
        "fifo_taps": fifo_taps,
        "lv_event_ok": lv_ok,
        "taps_total": get_state()["taps"],
    }


def _click_status(mode, seconds, inp):
    if seconds < 2:
        return "no timers"
    if inp["sdl_lv_taps"] >= 1:
        return "ok"
    if inp["fifo_taps"] >= 1:
        return "no click count" if mode == "sync" else "no manual clicks"
    return "no clicks"


def _result_payload(mode, click, state, broker_polls, inp):
    payload = {
        "mode": mode,
        "status": "ok" if click == "ok" else "fail",
        "click_status": click,
        "backend": _timer_backend(),
        "seconds": state["seconds"],
        "taps": state["taps"],
        "broker_polls": broker_polls,
        "sdl_stolen_taps": inp["sdl_stolen_taps"],
        "sdl_lv_taps": inp["sdl_lv_taps"],
        "fifo_taps": inp["fifo_taps"],
        "lv_event_ok": inp["lv_event_ok"],
        "taps_total": inp["taps_total"],
    }
    return payload


def _print_result(result):
    line = _RESULT_PREFIX + json.dumps(result, separators=(",", ":"))
    print(line)
    sys.stdout.flush()


def _deinit_display():
    try:
        import lv_utils

        inst = lv_utils.event_loop.current_instance()
        if inst is not None:
            inst.deinit()
    except Exception:
        pass


def _inject_quit_and_exit(pump, *, broker_poll=False, mode="?"):
    """
    Inject events.Quit via the queue read path, then pump LVGL so VirtualDevices
    drain the queue (production window-close path).  Process should not return.
    """
    import quit_inject

    if not quit_inject.inject_quit(broker_poll=broker_poll, pump_count=15, pump_delay=0.02, lvgl=True):
        _print_result(
            {
                "mode": mode,
                "status": "error",
                "backend": _timer_backend(),
                "error": "no QUEUE device for quit injection",
            }
        )
        raise SystemExit(1)

    pump(5, 0.02)
    if broker_poll:
        from board_config import broker

        broker.poll()

    _deinit_display()
    _print_result(
        {
            "mode": mode,
            "status": "error",
            "backend": _timer_backend(),
            "error": "events.Quit injection did not terminate process",
        }
    )
    raise SystemExit(1)


async def _inject_quit_and_exit_async(*, broker_poll=True, mode="?"):
    from board_config import broker

    queue_dev = _queue_device()
    if queue_dev is None:
        _print_result(
            {
                "mode": mode,
                "status": "error",
                "backend": _timer_backend(),
                "error": "no QUEUE device for quit injection",
            }
        )
        raise SystemExit(1)

    from eventsys import events

    pending = [events.Quit(events.QUIT)]
    orig_read = queue_dev._read

    def mock_read():
        if pending:
            return [pending.pop(0)]
        return None

    queue_dev._read = mock_read
    try:
        await _pump_lvgl_async(15, 0.02)
        if broker_poll:
            broker.poll()
    finally:
        queue_dev._read = orig_read

    _deinit_display()
    _print_result(
        {
            "mode": mode,
            "status": "error",
            "backend": _timer_backend(),
            "error": "events.Quit injection did not terminate process",
        }
    )
    raise SystemExit(1)


def _run_sync():
    import board_config

    board_config.TIMER_ASYNC = False

    from multimer import Timer, needs_pump
        _print_result(
            {
                "mode": "sync",
                "status": "skip",
                "reason": "needs_pump",
                "backend": _timer_backend(),
            }
        )
        return

    import display_driver  # noqa: F401
    from lv_test_timer_common import build_ui, get_state

    btn = build_ui()
    cx, cy = _button_center(btn)
    broker_polls = 0

    deadline = time.time() + _DURATION_S
    input_tests = None

    while time.time() < deadline:
        if input_tests is None and get_state()["seconds"] >= 2:
            input_tests = _run_input_tests(btn, cx, cy)
        time.sleep(0.01)

    state = get_state()
    inp = input_tests or {
        "sdl_stolen_taps": 0,
        "sdl_lv_taps": 0,
        "fifo_taps": 0,
        "lv_event_ok": False,
        "taps_total": state["taps"],
    }
    click = _click_status("sync", state["seconds"], inp)
    _print_result(_result_payload("sync", click, state, broker_polls, inp))
    _inject_quit_and_exit(_pump_lvgl, mode="sync")


def _run_queued():
    import board_config

    board_config.TIMER_ASYNC = False

    from board_config import broker

    import display_driver  # noqa: F401
    from lv_test_timer_common import build_ui, get_state
    from multimer import Timer, needs_pump, pump, sleep_ms

    timer_req = needs_pump()

    def queued_pump(n=5, delay_s=0):
        import lvgl as lv

        for _ in range(n):
            pump()
            if timer_req:
                broker.poll()
            if lv._nesting.value == 0:
                lv.task_handler()
            if delay_s:
                time.sleep(delay_s)

    btn = build_ui()
    cx, cy = _button_center(btn)
    broker_polls = 0

    deadline = time.time() + _DURATION_S
    input_tests = None

    while time.time() < deadline:
        pump()
        if timer_req:
            broker.poll()
        sleep_ms(1)

        if input_tests is None and get_state()["seconds"] >= 2:
            input_tests = _run_input_tests(btn, cx, cy, pump=queued_pump)

    state = get_state()
    inp = input_tests or {
        "sdl_stolen_taps": 0,
        "sdl_lv_taps": 0,
        "fifo_taps": 0,
        "lv_event_ok": False,
        "taps_total": state["taps"],
    }
    click = _click_status("queued", state["seconds"], inp)
    _print_result(_result_payload("queued", click, state, broker_polls, inp))
    _inject_quit_and_exit(queued_pump, broker_poll=timer_req, mode="queued")


def _run_async():
    import board_config

    board_config.TIMER_ASYNC = True

    from multimer import run

    try:
        import asyncio
    except ImportError:
        import uasyncio as asyncio

    result = {}

    async def main():
        from board_config import broker

        import display_driver  # noqa: F401
        from lv_test_timer_common import build_ui, get_state

        btn = build_ui()
        cx, cy = _button_center(btn)
        broker_polls = 0

        deadline = time.time() + _DURATION_S
        input_tests = None

        deadline = time.time() + _DURATION_S
        input_tests = None

        while time.time() < deadline:
            broker.poll()
            await asyncio.sleep(0)

            if input_tests is None and get_state()["seconds"] >= 2:
                input_tests = await _run_input_tests_async(btn, cx, cy)

        state = get_state()
        inp = input_tests or {
            "sdl_stolen_taps": 0,
            "sdl_lv_taps": 0,
            "fifo_taps": 0,
            "lv_event_ok": False,
            "taps_total": state["taps"],
        }
        click = _click_status("async", state["seconds"], inp)
        result.update(_result_payload("async", click, state, broker_polls, inp))
        _print_result(result)
        await _inject_quit_and_exit_async(mode="async")

    run(main)


_MODES = {
    "sync": _run_sync,
    "queued": _run_queued,
    "async": _run_async,
}


def main(mode=None):
    mode = mode or (sys.argv[1] if len(sys.argv) > 1 else "sync")
    if mode not in _MODES:
        print(f"Unknown mode {mode!r}; use sync, queued, or async")
        raise SystemExit(2)
    try:
        _MODES[mode]()
    except SystemExit:
        raise
    except Exception as exc:
        _print_result(
            {
                "mode": mode,
                "status": "error",
                "backend": _timer_backend(),
                "error": repr(exc),
            }
        )
        raise


if __name__ == "__main__":
    main()
