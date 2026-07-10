"""
Example-matrix test flag (importable on MicroPython and CPython).

example_test_wrapper.py / PyScript embed.html set ENABLED = True before
running bounded examples. On single-threaded hosts the harness cannot inject
quit from another thread; call :func:`install_deadline_hook` so
``multimer.sleep_ms`` / ``Runtime.poll`` cooperatively exit after ``DURATION_S``.

The underlying API is ``multimer.set_deadline_hook`` — development and
troubleshooting only; see docs/concepts/multimer.md.
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
    if _deadline_fired:
        return True
    import time

    now = time.time()
    if _start_s is None:
        _start_s = now
        return False
    if now - _start_s < float(DURATION_S):
        return False
    _deadline_fired = True
    try:
        import board_config

        rt = getattr(board_config, "runtime", None)
        if rt is not None:
            request = getattr(rt, "request_quit", None)
            if callable(request):
                request()
            elif not getattr(rt, "quit_requested", False):
                handle = getattr(rt, "_handle_quit", None)
                if callable(handle):
                    handle()
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
