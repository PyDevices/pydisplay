"""
Example-matrix test flag (importable on MicroPython and CPython).

example_test_wrapper.py / PyScript harness.html set ENABLED = True before
running bounded examples. On single-threaded hosts the harness cannot inject
quit from another thread; call :func:`install_deadline_hook` so
provider ``timer.sleep_ms`` / ``Runtime.poll`` cooperatively exit after
``DURATION_S``.

The underlying API is ``multimer.set_deadline_hook`` — development and
troubleshooting only; see https://github.com/PyDevices/pydevices/blob/main/docs/multimer.md.
"""

ENABLED = False
DURATION_S = 5.0

# Internal deadline bookkeeping (set by check_deadline).
_start_s = None
_deadline_fired = False


def check_deadline():
    """If test mode is active and ``DURATION_S`` elapsed, request runtime quit.

    Returns True when the deadline has fired (possibly just now).
    """
    global _start_s, _deadline_fired
    if not ENABLED:
        return False
    # Keep-alive only: do not arm or fire until ``run`` / ``run_forever`` is on
    # the stack. ``runtime is None`` must also wait — an early timer tick during
    # import used to start the clock, fire with no runtime, set
    # ``_deadline_fired``, then never quit once the blocking loop started.
    try:
        import sys

        module = sys.modules.get("display_driver")
        if module is not None and hasattr(module, "runtime"):
            rt = getattr(module, "runtime", None)
        else:
            appdev = sys.modules.get("appdev")
            rt = (
                getattr(getattr(appdev, "App", None), "_current", None)
                if appdev is not None
                else None
            )
    except Exception:
        rt = None
    # appdev.App uses ``_blocking_run_forever``; LVGL display_driver.Runtime
    # uses ``_blocking`` for the same "inside run_forever/run" gate.
    if rt is None or not (
        getattr(rt, "_blocking_run_forever", False) or getattr(rt, "_blocking", False)
    ):
        return False
    if getattr(rt, "_quit_requested", False):
        _deadline_fired = True
        return True
    import time

    now = time.time()
    if _start_s is None:
        _start_s = now
        return False
    if now - _start_s < float(DURATION_S):
        return False
    try:
        request = getattr(rt, "request_quit", None)
        if callable(request):
            request()
            _deadline_fired = True
        elif not getattr(rt, "quit_requested", False):
            handle = getattr(rt, "_handle_quit", None)
            if callable(handle):
                handle()
                _deadline_fired = True
    except Exception:
        pass
    return True


def install_deadline_hook():
    """Register :func:`check_deadline` with ``multimer.set_deadline_hook``.

    Harness-only. Clear with ``multimer.set_deadline_hook(None)`` when finished
    if the process will keep running.
    """
    try:
        import multimer

        multimer.set_deadline_hook(check_deadline)
    except ImportError:
        pass
