"""
Inject events.Quit through the QUEUE device read path (desktop SDL / PG backends).

Used by example_test_wrapper.py and lv_test_timer.py (kit mode).
Must stay importable on MicroPython, CircuitPython, and CPython.
"""


def queue_device():
    from board_config import runtime

    import eventsys

    for dev in runtime.devices:
        if dev.type == eventsys.HOST:
            return dev
    return None


def display_backend_name():
    try:
        from board_config import display_drv

        return type(display_drv).__name__
    except Exception as exc:
        return "error:{!r}".format(exc)


def deinit_display():
    try:
        import sys

        # Avoid importing display_driver (runs main()) if it was never loaded.
        dd = sys.modules.get("display_driver")
        if dd is None:
            return
        inst = dd.event_loop.current_instance()
        if inst is not None:
            inst.deinit()
    except Exception:
        pass


def service_host_events(count=15, delay_s=0.02, broker_poll=True):
    """Service host display / runtime events only."""
    try:
        import time
    except ImportError:
        return

    runtime = None
    if broker_poll:
        try:
            from board_config import runtime as _broker

            runtime = _broker
        except Exception:
            runtime = None

    for _ in range(count):
        if runtime is not None:
            try:
                runtime.poll()
            except Exception:
                pass
        if delay_s:
            time.sleep(delay_s)


def pump_lvgl(count=5, delay_s=0):
    try:
        import time

        import lvgl as lv
    except ImportError:
        service_host_events(count, delay_s or 0.02)
        return

    if not lv.is_initialized():
        service_host_events(count, delay_s or 0.02)
        return

    for _ in range(count):
        if lv._nesting.value == 0:
            lv.task_handler()
        if delay_s:
            time.sleep(delay_s)


def inject_synthetic_touch(*, broker_poll=False, pump_count=20, pump_delay=0.02):
    """
    Deliver synthetic mouse clicks at corners and center through the QUEUE device.

    Used by example_test_wrapper for quit=inject examples (touch tests, drag demos).
    """
    from eventsys import events

    try:
        from board_config import display_drv
    except Exception:
        return False

    queue_dev = queue_device()
    if queue_dev is None:
        return False

    w = display_drv.width
    h = display_drv.height
    points = (
        (max(1, w // 8), max(1, h // 8)),
        (max(1, w - w // 8), max(1, h // 8)),
        (max(1, w // 8), max(1, h - h // 8)),
        (max(1, w - w // 8), max(1, h - h // 8)),
        (w // 2, h // 2),
    )
    pending = []
    for pos in points:
        pending.append(events.Button(events.MOUSEBUTTONDOWN, pos, 1, False, 0))
        pending.append(events.Button(events.MOUSEBUTTONUP, pos, 1, False, 0))

    orig_read = queue_dev._read

    def mock_read():
        if pending:
            return [pending.pop(0)]
        return orig_read()

    queue_dev._read = mock_read
    try:
        service_host_events(pump_count, pump_delay, broker_poll=broker_poll)
    finally:
        queue_dev._read = orig_read
    return True


def inject_quit(*, broker_poll=True, pump_count=15, pump_delay=0.02, lvgl=False, deinit=True):
    """
    Mock QUEUE read to deliver one Quit event, then pump runtime / multimer / LVGL.

    Returns True if injection was attempted (QUEUE device existed).
    The caller should verify the process exits; if still running, quit was not handled.
    """
    from eventsys import events

    queue_dev = queue_device()
    if queue_dev is None:
        return False

    pending = [events.Quit(events.QUIT)]
    orig_read = queue_dev._read

    def mock_read():
        if pending:
            return [pending.pop(0)]
        return orig_read()

    queue_dev._read = mock_read
    try:
        if lvgl:
            pump_lvgl(pump_count, pump_delay)
        else:
            service_host_events(pump_count, pump_delay, broker_poll=broker_poll)
        if broker_poll:
            try:
                from board_config import runtime

                runtime.poll()
            except Exception:
                pass
    finally:
        if not pending:
            queue_dev._read = orig_read

    if deinit:
        deinit_display()
    return True
