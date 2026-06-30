# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
multimer — cross-platform Timer library for *Python.

Substitutes for ``machine.Timer`` on MicroPython microcontrollers, MicroPython
Unix, CPython, and CircuitPython.  Provides portable ``ticks_*`` and
``sleep_ms``, optional asyncio ``AsyncTimer``, and a single ``pump()`` call for
cooperative backends.

Quick start (sync)::

    import multimer

    tim = multimer.Timer(-1)
    tim.init(mode=multimer.PERIODIC, period=500, callback=lambda t: print("."))
    while True:
        if multimer.needs_pump():
            multimer.pump()
        do_work()

Quick start (async)::

    import multimer

    async def main():
        tim = multimer.AsyncTimer(-1)
        tim.init(mode=multimer.PERIODIC, period=33, callback=on_tick)
        while True:
            do_work()
            await multimer.sleep_ms(0)

    multimer.run(main)
"""

import sys

from ._capabilities import (
    UnsupportedPlatformError,
    backend_name,
    capabilities,
    init_capabilities,
    needs_pump,
)
from ._schedule import _drain_schedule, schedule
from ._ticks import sleep_ms as _sync_sleep_ms
from ._ticks import ticks_add, ticks_diff, ticks_less, ticks_ms

try:
    from ._polling import _tick as _polling_tick
except ImportError:
    _polling_tick = None

_BACKEND = None
_NEEDS_PUMP = False

try:
    from machine import Timer as _MachineTimer

    Timer = _MachineTimer
    _BACKEND = "machine"
    _NEEDS_PUMP = False
except ImportError:
    Timer = None
    if sys.implementation.name == "micropython":
        try:
            from ._posix import Timer

            _BACKEND = Timer.BACKEND
            _NEEDS_PUMP = Timer.NEEDS_PUMP
        except ImportError:
            try:
                from ._threading import Timer

                _BACKEND = Timer.BACKEND
                _NEEDS_PUMP = Timer.NEEDS_PUMP
            except ImportError:
                from ._polling import Timer

                _BACKEND = Timer.BACKEND
                _NEEDS_PUMP = Timer.NEEDS_PUMP
    elif sys.implementation.name == "cpython":
        try:
            from ._posix import Timer

            _BACKEND = Timer.BACKEND
            _NEEDS_PUMP = Timer.NEEDS_PUMP
        except ImportError:
            try:
                from ._threading import Timer

                _BACKEND = Timer.BACKEND
                _NEEDS_PUMP = Timer.NEEDS_PUMP
            except ImportError:
                from ._sdl2 import Timer

                _BACKEND = Timer.BACKEND
                _NEEDS_PUMP = Timer.NEEDS_PUMP
    elif sys.implementation.name == "circuitpython":
        from ._threading import Timer

        _BACKEND = Timer.BACKEND
        _NEEDS_PUMP = Timer.NEEDS_PUMP

if Timer is None:
    raise UnsupportedPlatformError("multimer: no Timer backend available on this platform")

init_capabilities(backend=_BACKEND, needs_pump=_NEEDS_PUMP)

try:
    from ._async import AsyncTimer, run, run_forever_async
    from ._async import dual_main as _async_dual_main
    from ._async import sleep_ms as _async_sleep_ms

    init_capabilities(backend=_BACKEND, needs_pump=_NEEDS_PUMP)
except ImportError:
    AsyncTimer = None
    run = None
    _async_dual_main = None
    run_forever_async = None
    _async_sleep_ms = None

PERIODIC = Timer.PERIODIC
ONE_SHOT = Timer.ONE_SHOT

_next_timer_id = 1


def _drain_native_scheduler(max_items=None):
    try:
        import usdl2

        pump_scheduler = getattr(usdl2, "pump_scheduler", None)
        if pump_scheduler is None:
            return 0
        return pump_scheduler(max_items)
    except ImportError:
        return 0


def pump(max_items=None):
    """Drain the schedule queue and fire due cooperative timers.

    Returns the number of callbacks dispatched.
    """
    n = _drain_schedule(max_items)
    n_native = 0
    remaining = None if max_items is None else max_items - n
    if remaining is None or remaining > 0:
        n_native = _drain_native_scheduler(remaining)
        n += n_native
    if _polling_tick is not None:
        if max_items is None:
            n += _polling_tick()
        else:
            remaining = max_items - n
            if remaining > 0:
                n += _polling_tick(remaining)
    return n


def _async_loop_running(aio):
    """Return True when ``aio`` has a running event loop (uasyncio or asyncio)."""
    if hasattr(aio, "get_running_loop"):
        try:
            aio.get_running_loop()
            return True
        except RuntimeError:
            return False
    current_task = getattr(aio, "current_task", None)
    if current_task is not None:
        try:
            return current_task() is not None
        except RuntimeError:
            return False
    return False


def sleep_ms(ms):
    """Sleep for ``ms`` milliseconds.

    In a running asyncio event loop, returns an awaitable coroutine — use
    ``await multimer.sleep_ms(ms)``.  Otherwise blocks and advances cooperative
    sync timers.
    """

    # #region agent log
    def _agent_log(message, data, hypothesis_id):
        try:
            import json
            import time

            with open(
                "/home/brad/github/pydisplay/.cursor/debug-39b49e.log", "a", encoding="utf-8"
            ) as _f:
                _f.write(
                    json.dumps(
                        {
                            "sessionId": "39b49e",
                            "hypothesisId": hypothesis_id,
                            "location": "multimer/__init__.py:sleep_ms",
                            "message": message,
                            "data": data,
                            "timestamp": int(time.time() * 1000),
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass

    # #endregion
    if _async_sleep_ms is not None:
        try:
            from ._async import _require_asyncio

            aio = _require_asyncio()
            has_grl = hasattr(aio, "get_running_loop")
            has_ct = hasattr(aio, "current_task")
            ct = aio.current_task() if has_ct else None
            # #region agent log
            _agent_log(
                "sleep_ms asyncio probe",
                {
                    "ms": ms,
                    "has_get_running_loop": has_grl,
                    "has_current_task": has_ct,
                    "current_task": repr(ct),
                },
                "H1",
            )
            # #endregion
            if _async_loop_running(aio):
                # #region agent log
                _agent_log(
                    "async branch via loop detection",
                    {"ms": ms, "used_get_running_loop": has_grl},
                    "H1",
                )
                # #endregion
                return _async_sleep_ms(ms)
        except ImportError as err:
            # #region agent log
            _agent_log("asyncio import failed", {"err": repr(err)}, "H2")
            # #endregion
    # #region agent log
    _agent_log("sync branch (no awaitable returned)", {"ms": ms}, "H1")
    # #endregion
    _sync_sleep_ms(ms)


def periodic(callback, period=33, *, async_=False, verbose=False):
    """Create and start a periodic timer.

    Args:
        callback: Called as ``callback(timer)`` on each tick.
        period: Interval in milliseconds (default 33 ms).
        async_: Use ``AsyncTimer`` (requires a running event loop at init).
        verbose: Print backend and start info when True.
    """
    global _next_timer_id
    if async_:
        if AsyncTimer is None:
            raise ImportError("multimer async support requires asyncio or uasyncio")
        TimerCls = AsyncTimer
    else:
        TimerCls = Timer

    if sys.platform == "rp2":
        timer_id = -1
    else:
        timer_id = _next_timer_id
        _next_timer_id += 1
    t = TimerCls(timer_id)

    def _timer_cb(_t):
        callback(t)

    t.init(mode=TimerCls.PERIODIC, period=period, callback=_timer_cb)
    if verbose:
        mod = getattr(TimerCls, "__module__", "?")
        name = getattr(TimerCls, "__qualname__", getattr(TimerCls, "__name__", "?"))
        print(f"multimer: backend {mod}.{name}")
        print(f"multimer: timer started (id={timer_id}, period={period})")
        if not async_ and needs_pump():
            print("multimer: call pump() from your main loop")
    return t


def run_forever(poll=None, *, delay_ms=1):
    """Run the standard sync main loop until ``poll()`` returns True or interrupted."""
    while True:
        pump()
        if poll is not None and poll() is True:
            break
        _sync_sleep_ms(delay_ms)


def dual_main(sync_main, async_main, *, async_mode=False):
    """Run ``sync_main()`` or schedule ``async_main()`` under asyncio.

    Startup is posted with ``schedule`` so MicroPython can finish import before
    timers run; on CPython the main thread runs the callback immediately.
    """

    def _run(_=None):
        if not async_mode:
            sync_main()
            return
        if _async_dual_main is None:
            sync_main()
            return
        _async_dual_main(sync_main, async_main, async_mode=True)

    schedule(_run, None)


from ._timerbase import ON_CALLBACK_ERROR  # noqa: E402
