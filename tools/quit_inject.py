"""
Inject events.Quit through the QUEUE device read path (desktop SDL / PG backends).

Used by example_test_wrapper.py and lv_test_timer_harness.py.
Must stay importable on MicroPython, CircuitPython, and CPython.
"""


def queue_device():
    from board_config import broker

    import eventsys

    for dev in broker.devices:
        if dev.type == eventsys.QUEUE:
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
        import lv_utils

        inst = lv_utils.event_loop.current_instance()
        if inst is not None:
            inst.deinit()
    except Exception:
        pass


def pump_multimer(count=15, delay_s=0.02, broker_poll=True):
    try:
        from multimer import pump, sleep_ms
    except ImportError:
        pump = None
        try:
            import time

            sleep_ms = lambda ms: time.sleep(ms / 1000.0)  # noqa: E731
        except ImportError:
            return

    broker = None
    if broker_poll:
        try:
            from board_config import broker as _broker

            broker = _broker
        except Exception:
            broker = None

    ms = int(delay_s * 1000) if delay_s else 0
    for _ in range(count):
        if broker is not None:
            broker.poll()
        if pump is not None:
            pump()
        if ms:
            sleep_ms(ms)


def pump_lvgl(count=5, delay_s=0):
    try:
        import time

        import lvgl as lv
    except ImportError:
        pump_multimer(count, delay_s or 0.02)
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
        pump_multimer(pump_count, pump_delay, broker_poll=broker_poll)
    finally:
        queue_dev._read = orig_read
    return True


def inject_quit(*, broker_poll=True, pump_count=15, pump_delay=0.02, lvgl=False):
    """
    Mock QUEUE read to deliver one Quit event, then pump broker / multimer / LVGL.

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
        return None

    queue_dev._read = mock_read
    try:
        if lvgl:
            pump_lvgl(pump_count, pump_delay)
        else:
            pump_multimer(pump_count, pump_delay, broker_poll=broker_poll)
        if broker_poll and not lvgl:
            try:
                from board_config import broker

                broker.poll()
            except Exception:
                pass
    finally:
        queue_dev._read = orig_read

    deinit_display()
    return True
