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

except (ImportError, NameError):
    import time

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

        except (ImportError, NameError, NotImplementedError):
            from time import monotonic as _monotonic

            def ticks_ms():
                return int(_monotonic() * 1000) & _TICKS_MAX


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


def sleep_ms(ms):
    """Block for ``ms`` milliseconds."""
    try:
        from time import sleep_ms as _time_sleep_ms

        _time_sleep_ms(ms)
    except ImportError:
        import time

        time.sleep(ms / 1000)


_sleep_ms = sleep_ms
