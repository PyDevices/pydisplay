# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Jeff Epler for Adafruit Industries
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Adafruit-compatible wrapping millisecond ticks."""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


_TICKS_PERIOD = const(1 << 29)
_TICKS_MAX = const(_TICKS_PERIOD - 1)
_TICKS_HALFPERIOD = const(_TICKS_PERIOD // 2)

_needs_software_ticks_math = True

try:
    from supervisor import ticks_ms as _supervisor_ticks_ms

    def ticks_ms():
        return _supervisor_ticks_ms()

    def monotonic():
        return _supervisor_ticks_ms() / 1000

except (ImportError, NameError):
    import time

    if _time_monotonic := getattr(time, "monotonic", None):

        def monotonic():
            return _time_monotonic()

    elif _time_monotonic_ns := getattr(time, "monotonic_ns", None):

        def monotonic():
            return _time_monotonic_ns() / 1_000_000_000

    if _time_ticks_ms := getattr(time, "ticks_ms", None):
        if getattr(time, "ticks_add", None) and getattr(time, "ticks_diff", None):
            ticks_ms = _time_ticks_ms
            ticks_add = time.ticks_add
            ticks_diff = time.ticks_diff
            _needs_software_ticks_math = False
        else:

            def ticks_ms():
                return _time_ticks_ms() & _TICKS_MAX

    else:
        try:
            from time import monotonic_ns as _monotonic_ns

            _monotonic_ns()

            def ticks_ms():
                return (_monotonic_ns() // 1_000_000) & _TICKS_MAX

            if "monotonic" not in globals():

                def monotonic():
                    return _monotonic_ns() / 1_000_000_000

        except (ImportError, NameError, NotImplementedError):
            from time import monotonic as _monotonic

            def ticks_ms():
                return int(_monotonic() * 1000) & _TICKS_MAX

            if "monotonic" not in globals():

                def monotonic():
                    return _monotonic()

    if "monotonic" not in globals():

        def monotonic():
            return _time_ticks_ms() / 1000


if _needs_software_ticks_math:

    def ticks_add(ticks, delta):
        """Add a delta to a base number of ticks, performing wraparound at 2**29ms."""
        if -_TICKS_HALFPERIOD < delta < _TICKS_HALFPERIOD:
            return (ticks + delta) % _TICKS_PERIOD
        raise OverflowError("ticks interval overflow")

    def ticks_diff(ticks1, ticks2):
        """Compute the signed difference between two ticks values."""
        diff = (ticks1 - ticks2) & _TICKS_MAX
        diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
        return diff


def ticks_less(ticks1, ticks2):
    """Return True if ticks1 is before ticks2."""
    return ticks_diff(ticks1, ticks2) < 0


def _raw_sleep_ms(ms):
    try:
        from time import sleep_ms as _time_sleep_ms

        _time_sleep_ms(ms)
    except ImportError:
        import time

        time.sleep(ms / 1000)


# Optional development/troubleshooting hook only — not part of normal app use.
# Single-threaded hosts (e.g. browser WASM) cannot inject quit from another
# thread; a test harness may register a zero-arg callable invoked from
# sleep_ms (and optionally from an app poll loop) to enforce a wall-clock
# deadline. Production code should leave this unset (None).
_deadline_hook = None


def set_deadline_hook(hook):
    """Register or clear a cooperative deadline hook (dev/troubleshooting only).

    This is **not** an application API. Use it only from test harnesses or
    interactive debugging when you need a wall-clock deadline on hosts that
    cannot run a background quit thread (for example browser WASM).

    ``hook`` is a zero-arg callable, or ``None`` to clear. :func:`sleep_ms`
    calls it before and after sleeping; callers may also invoke
    :func:`run_deadline_hook` from a poll loop. The hook's return value is
    passed through by :func:`run_deadline_hook`.

    Example (harness)::

        def on_deadline():
            runtime.request_quit()
            return True

        multimer.set_deadline_hook(on_deadline)
        # ... run bounded demo ...
        multimer.set_deadline_hook(None)
    """
    global _deadline_hook
    _deadline_hook = hook


def run_deadline_hook():
    """Invoke the registered deadline hook, if any (dev/troubleshooting only).

    Returns the hook's result, or ``False`` when no hook is registered.
    Prefer leaving this to :func:`sleep_ms` unless you are writing harness
    code that also polls without sleeping.
    """
    hook = _deadline_hook
    if hook is None:
        return False
    return hook()


def sleep_ms(ms):
    """Block for ``ms`` milliseconds.

    Also runs any registered :func:`set_deadline_hook` callback (harness use
    only) before and after the wait, and advances cooperative timer queues.
    """
    run_deadline_hook()
    from ._schedule import _run_pending
    from ._select import _drain as _backend_drain
    from ._select import _sleep_ms as _backend_sleep_ms

    _run_pending()
    if _backend_drain is not None:
        _backend_drain()
    if _backend_sleep_ms is not None:
        _backend_sleep_ms(ms)
    else:
        _raw_sleep_ms(ms)
    run_deadline_hook()
    _run_pending()
    if _backend_drain is not None:
        _backend_drain()


_sleep_ms = sleep_ms
