# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Probe public multimer Timer APIs available on this Python port.

Public surfaces exercised (when importable on the host):

- ``machine.Timer`` — MCU hardware (not multimer; listed for comparison)
- ``multimer.Timer`` — platform default backend
- ``multimer.AsyncTimer`` — asyncio / uasyncio (sleep and yield-loop styles)

Development-only optional probes of private backends are behind
``MULTIMER_PROBE_BACKENDS=1`` (not for production).

Run the full desktop matrix::

    python tools/run_test_timers.py

Each probe is isolated so one failure does not stop the rest. Imports that
fail are reported as SKIP.
"""

import os
import sys
import time


def _bootstrap_src_path():
    """Allow ``python tools/test_timers.py`` from a dev clone (``src/lib`` on path)."""
    f = __file__.replace("\\", "/")
    if f.endswith(".py"):
        f = f[:-3]
    if f.endswith("/tools/test_timers"):
        lib = f[: -len("/tools/test_timers")] + "/src/lib"
    else:
        lib = "../src/lib"
    try:
        os.stat(lib)
    except Exception:
        return
    if lib not in sys.path:
        sys.path.insert(0, lib)


_bootstrap_src_path()

from multimer import sleep_ms  # noqa: E402

TEST_PERIOD_MS = 50
TEST_DURATION_MS = 300
MIN_CALLBACKS = 2


def _probe_backends_enabled():
    """Development-only private backend probes (not available on all ports)."""
    environ = getattr(os, "environ", None)
    if environ is None:
        return False
    try:
        return environ.get("MULTIMER_PROBE_BACKENDS", "") == "1"
    except Exception:
        return False


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


def _wait_ms(ms):
    deadline = time.monotonic() + (ms / 1000.0)
    while time.monotonic() < deadline:
        sleep_ms(10)


def _run_timer_test(TimerClass):
    """
    Start a periodic timer, wait, stop, verify fire.

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
    _wait_ms(TEST_DURATION_MS)
    timer.deinit()

    count = counter[0]
    if count >= MIN_CALLBACKS:
        if received[0] is not timer:
            return "FAIL", f"callback arg is not timer instance: {received[0]!r}"
        return "PASS", f"{count} callbacks in {TEST_DURATION_MS} ms"
    return "FAIL", f"expected >={MIN_CALLBACKS} callbacks, got {count}"


async def _run_async_timer_test(TimerClass):
    import asyncio

    counter = [0]

    def callback(_timer):
        counter[0] += 1

    timer = TimerClass(_timer_id())
    timer.init(mode=TimerClass.PERIODIC, period=TEST_PERIOD_MS, callback=callback)
    await asyncio.sleep(TEST_DURATION_MS / 1000)
    timer.deinit()
    return counter[0]


def _run_async_loop_test(TimerClass):
    """Exercise AsyncTimer while the main thread also does sync work."""
    import asyncio

    counter = [0]

    def callback(_timer):
        counter[0] += 1

    async def main():
        timer = TimerClass(_timer_id())
        timer.init(mode=TimerClass.PERIODIC, period=TEST_PERIOD_MS, callback=callback)
        elapsed = 0
        while elapsed < TEST_DURATION_MS:
            time.sleep(0.01)  # noqa: ASYNC251 — intentional sync work on the event-loop thread
            await asyncio.sleep(0)
            elapsed += 10
        timer.deinit()
        return counter[0]

    return asyncio.run(main())


def _run_async_timer_test_sync(TimerClass):
    import asyncio

    return asyncio.run(_run_async_timer_test(TimerClass))


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


def _import_async_timer():
    from multimer import AsyncTimer

    return AsyncTimer


def _import_multimer_timer():
    from multimer import Timer

    return Timer


def _import_backend_timer(backend_name):
    mod = __import__(
        f"multimer._backends.{backend_name}",
        None,
        None,
        ("Timer",),
    )
    return mod.Timer


def main():
    _print_platform()

    probes = [
        ("machine.Timer", _import_machine_timer, False, False),
        ("AsyncTimer", _import_async_timer, True, False),
        ("AsyncTimer (yield loop)", _import_async_timer, False, True),
        ("multimer.Timer (default)", _import_multimer_timer, False, False),
    ]

    if _probe_backends_enabled():
        print("development backend probes enabled (MULTIMER_PROBE_BACKENDS=1)")
        print()
        for name in ("librt", "win32", "threading", "polling"):
            probes.append(
                (
                    f"_backends.{name}.Timer",
                    lambda n=name: _import_backend_timer(n),
                    False,
                    False,
                )
            )

    for name, import_fn, async_test, async_loop_test in probes:
        _probe(name, import_fn, async_test=async_test, async_loop_test=async_loop_test)


if __name__ == "__main__":
    main()
