# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Probe every multimer Timer backend available on this Python port.

From ``src/`` with ``lib.path`` configured::

    python
    >>> import lib.path
    >>> import test_timers

Each implementation is imported and exercised inside its own try block so one
failure does not stop the rest.  Implementations that cannot be imported are
reported as SKIP.
"""

import sys

from multimer._schedule import run_queued
from multimer._ticks import sleep_ms as wait_ms

TEST_PERIOD_MS = 50
TEST_DURATION_MS = 300
MIN_CALLBACKS = 2


def _timer_id():
    return -1 if sys.platform == "rp2" else 1


def _print_platform():
    impl = getattr(sys, "implementation", None)
    name = impl.name if impl else "unknown"
    version = impl.version if impl else "unknown"
    print("multimer timer probe")
    print(f"  implementation: {name} {version}")
    print(f"  platform: {sys.platform}")
    print(f"  python: {sys.version.split()[0]}")
    print()


def _print_error(label, err):
    print(f"  {label}: {type(err).__name__}: {err}")


def _import_timer(module_name):
    """Import a Timer class from a multimer backend module."""
    mod = __import__(f"multimer.{module_name}", None, None, ("Timer",))
    return mod.Timer


def _run_timer_test(TimerClass):
    """
    Start a periodic timer, wait, stop, and verify callbacks fired.

    Returns:
        tuple[str, str | int]: (status, detail) where status is PASS, FAIL, or SKIP.
    """
    if TimerClass is None:
        return "SKIP", "Timer is None on this platform"

    counter = [0]
    received = [None]

    def callback(_timer):
        received[0] = _timer
        counter[0] += 1

    timer = TimerClass(_timer_id())
    timer.init(mode=TimerClass.PERIODIC, period=TEST_PERIOD_MS, callback=callback)

    requires_run = getattr(TimerClass, "REQUIRES_RUN_QUEUED", False)
    elapsed = 0
    while elapsed < TEST_DURATION_MS:
        if requires_run:
            run_queued()
        wait_ms(10)
        elapsed += 10

    timer.deinit()

    count = counter[0]
    if count >= MIN_CALLBACKS:
        if received[0] is not timer:
            return "FAIL", f"callback arg is not timer instance: {received[0]!r}"
        return "PASS", f"{count} callbacks in {TEST_DURATION_MS} ms"
    return "FAIL", f"expected >={MIN_CALLBACKS} callbacks, got {count}"


async def _run_async_timer_test(TimerClass):
    from multimer.aio import _sleep_ms

    counter = [0]

    def callback(_timer):
        counter[0] += 1

    timer = TimerClass(_timer_id())
    timer.init(mode=TimerClass.PERIODIC, period=TEST_PERIOD_MS, callback=callback)
    await _sleep_ms(TEST_DURATION_MS)
    timer.deinit()
    return counter[0]


def _run_async_loop_test(TimerClass):
    """Exercise Timer + run_queued() in a sync-work / async-yield loop."""
    from multimer.aio import run, run_queued

    counter = [0]

    def callback(_timer):
        counter[0] += 1

    async def main():
        timer = TimerClass(_timer_id())
        timer.init(mode=TimerClass.PERIODIC, period=TEST_PERIOD_MS, callback=callback)
        elapsed = 0
        while elapsed < TEST_DURATION_MS:
            wait_ms(10)
            await run_queued()
            elapsed += 10
        timer.deinit()
        return counter[0]

    return run(main)


def _run_async_timer_test_sync(TimerClass):
    try:
        import asyncio
    except ImportError:
        try:
            import uasyncio as asyncio
        except ImportError:
            raise ImportError("asyncio or uasyncio required") from None

    if hasattr(asyncio, "run"):
        return asyncio.run(_run_async_timer_test(TimerClass))
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_run_async_timer_test(TimerClass))


def _probe(name, import_fn, *, async_test=False, async_loop_test=False):
    print(f"{name}:")
    try:
        TimerClass = import_fn()
    except ImportError as err:
        print("  SKIP (import)")
        _print_error("reason", err)
        print()
        return
    except Exception as err:
        print("  SKIP (import)")
        _print_error("reason", err)
        print()
        return

    print(f"  REQUIRES_RUN_QUEUED: {getattr(TimerClass, 'REQUIRES_RUN_QUEUED', False)}")

    try:
        if async_loop_test:
            count = _run_async_loop_test(TimerClass)
            if count >= MIN_CALLBACKS:
                status, detail = "PASS", f"{count} callbacks in {TEST_DURATION_MS} ms"
            else:
                status, detail = "FAIL", f"expected >={MIN_CALLBACKS} callbacks, got {count}"
        elif async_test:
            count = _run_async_timer_test_sync(TimerClass)
            if count >= MIN_CALLBACKS:
                status, detail = "PASS", f"{count} callbacks in {TEST_DURATION_MS} ms"
            else:
                status, detail = "FAIL", f"expected >={MIN_CALLBACKS} callbacks, got {count}"
        else:
            status, detail = _run_timer_test(TimerClass)
    except Exception as err:
        print("  FAIL (runtime)")
        _print_error("reason", err)
        try:
            sys.print_exception(err)
        except AttributeError:
            pass
        print()
        return

    print(f"  {status}: {detail}")
    print()


def _import_machine_timer():
    from machine import Timer

    return Timer


def _import_ffi_timer():
    return _import_timer("_ffi")


def _import_sdl2_timer():
    return _import_timer("_sdl2")


def _import_threading_timer():
    return _import_timer("_threading")


def _import_ctypes_timer():
    return _import_timer("_ctypes")


def _import_aio_timer():
    return _import_timer("aio")


def _import_polling_timer():
    return _import_timer("_polling")


def _import_multimer_timer():
    from multimer import Timer

    return Timer


def main():
    _print_platform()

    probes = (
        ("machine.Timer", _import_machine_timer, False, False),
        ("_ffi.Timer", _import_ffi_timer, False, False),
        ("_sdl2.Timer", _import_sdl2_timer, False, False),
        ("_threading.Timer", _import_threading_timer, False, False),
        ("_polling.Timer", _import_polling_timer, False, False),
        ("_ctypes.Timer", _import_ctypes_timer, False, False),
        ("aio.Timer", _import_aio_timer, True, False),
        ("aio.Timer (run_queued loop)", _import_aio_timer, False, True),
        ("multimer.Timer (default)", _import_multimer_timer, False, False),
    )

    for probe in probes:
        name, import_fn, async_test, async_loop_test = probe
        _probe(name, import_fn, async_test=async_test, async_loop_test=async_loop_test)


main()
