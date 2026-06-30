# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Jeff Epler for Adafruit Industries
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cross-platform millisecond tick helpers for multimer."""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


_TICKS_PERIOD = const(1 << 29)
_TICKS_MAX = const(_TICKS_PERIOD - 1)
_TICKS_HALFPERIOD = const(_TICKS_PERIOD // 2)

# ticks_ms sources, in order:
#
#  - supervisor.ticks_ms (CircuitPython on supported boards)
#  - time.ticks_ms with time.ticks_add/time.ticks_diff (MicroPython)
#  - time.monotonic_ns or time.monotonic fallbacks (CPython and older ports)

_needs_software_ticks_math = True

try:
    from supervisor import ticks_ms as _supervisor_ticks_ms

    def ticks_ms() -> int:
        return _supervisor_ticks_ms()

except (ImportError, NameError):
    import time

    if _time_ticks_ms := getattr(time, "ticks_ms", None):
        if getattr(time, "ticks_add", None) and getattr(time, "ticks_diff", None):
            ticks_ms = _time_ticks_ms
            ticks_add = time.ticks_add
            ticks_diff = time.ticks_diff
            _needs_software_ticks_math = False
        else:

            def ticks_ms() -> int:
                return _time_ticks_ms() & _TICKS_MAX

    else:
        try:
            from time import monotonic_ns as _monotonic_ns

            _monotonic_ns()

            def ticks_ms() -> int:
                return (_monotonic_ns() // 1_000_000) & _TICKS_MAX

        except (ImportError, NameError, NotImplementedError):
            from time import monotonic as _monotonic

            def ticks_ms() -> int:
                return int(_monotonic() * 1000) & _TICKS_MAX


if _needs_software_ticks_math:

    def ticks_add(ticks: int, delta: int) -> int:
        "Add a delta to a base number of ticks, performing wraparound at 2**29ms."
        if -_TICKS_HALFPERIOD < delta < _TICKS_HALFPERIOD:
            return (ticks + delta) % _TICKS_PERIOD
        raise OverflowError("ticks interval overflow")

    def ticks_diff(ticks1: int, ticks2: int) -> int:
        """Compute the signed difference between two ticks values,
        assuming that they are within 2**28 ticks"""
        diff = (ticks1 - ticks2) & _TICKS_MAX
        diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
        return diff


def ticks_less(ticks1: int, ticks2: int) -> bool:
    """Return true if ticks1 is before ticks2 and false otherwise,
    assuming that they are within 2**28 ticks"""
    return ticks_diff(ticks1, ticks2) < 0


try:
    from time import sleep_ms as _time_sleep_ms
except ImportError:
    import time

    def _time_sleep_ms(ms):
        time.sleep(ms / 1000)


def _tick_polling_timers():
    try:
        from ._polling import _tick

        _tick()
    except ImportError:
        pass


def _tick_native_scheduler():
    try:
        import usdl2

        pump_scheduler = getattr(usdl2, "pump_scheduler", None)
        if pump_scheduler is not None:
            pump_scheduler(8)
    except ImportError:
        pass


def sleep_ms(ms):
    if ms <= 0:
        _tick_polling_timers()
        _tick_native_scheduler()
        return

    end = ticks_add(ticks_ms(), ms)
    while True:
        _tick_polling_timers()
        _tick_native_scheduler()
        delay = ticks_diff(end, ticks_ms())
        if delay <= 0:
            break
        chunk = delay if delay < 10 else 10
        _time_sleep_ms(chunk)
        _tick_native_scheduler()
