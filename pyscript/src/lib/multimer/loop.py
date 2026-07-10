# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Small optional application-loop helpers."""


def run_forever(poll, delay_ms=20):
    """Run a polling loop until ``poll`` returns true."""
    timer_async = False
    try:
        from board_config import runtime

        timer_async = runtime is not None and runtime.timer_async
    except ImportError:
        pass

    if timer_async:

        async def _main():
            await run_forever_async(poll, delay_ms=delay_ms)

        return run(_main)

    from . import sleep_ms

    while True:
        if poll():
            break
        sleep_ms(delay_ms)


async def run_forever_async(poll, delay_ms=20):
    """Async version of ``run_forever``."""
    from . import asyncio
    from ._schedule import _run_pending
    from ._select import _drain as _backend_drain

    while True:
        if poll():
            break
        _run_pending()
        if _backend_drain is not None:
            _backend_drain()
        await asyncio.sleep(delay_ms / 1000)  # type: ignore[misc]


def _event_loop_running():
    try:
        from . import asyncio

        if hasattr(asyncio, "get_running_loop"):
            asyncio.get_running_loop()
            return True
    except (ImportError, RuntimeError):
        pass
    return False


def _coroutine_factory(coro_or_fn):
    if hasattr(coro_or_fn, "__await__"):
        return lambda: coro_or_fn

    try:
        import inspect

        if inspect.iscoroutinefunction(coro_or_fn):
            return coro_or_fn
    except (ImportError, AttributeError):
        pass

    try:
        from . import asyncio

        if hasattr(asyncio, "iscoroutinefunction") and asyncio.iscoroutinefunction(coro_or_fn):
            return coro_or_fn
    except (ImportError, AttributeError):
        pass

    # MicroPython: inspect may be missing; zero-arg async entries return generators.
    try:
        trial = coro_or_fn()
        if hasattr(trial, "__await__"):
            return coro_or_fn
        if type(trial).__name__ in ("generator", "coroutine"):
            return coro_or_fn
    except TypeError:
        pass

    raise TypeError("run() expects a coroutine function or coroutine object")


def _arm_runtime_async_refresh():
    try:
        from board_config import runtime
    except ImportError:
        return
    if runtime is not None:
        runtime.arm_async_refresh()


def run(coro_or_fn):
    """
      Run a coroutine to completion.

    On hosts with a running loop (Jupyter, PyScript), schedules the coroutine as a
      background task and returns immediately. Otherwise blocks until the coroutine
      finishes (desktop SDL, MCU).
    """
    factory = _coroutine_factory(coro_or_fn)

    async def _runner():
        _arm_runtime_async_refresh()
        return await factory()

    if _event_loop_running():
        from . import asyncio

        return asyncio.create_task(_runner())

    from . import asyncio

    if hasattr(asyncio, "run"):
        return asyncio.run(_runner())

    from . import _mpasyncio

    return _mpasyncio.run(_runner())


def dual_main(sync_main, async_main, async_mode=False):
    """
    Start either a sync or async application entrypoint.

    In async mode, the async entrypoint is scheduled on the active multimer
    asyncio loop and the created task is returned. When no loop is running,
    ``run()`` blocks until ``async_main`` completes (desktop SDL/PG).
    """
    if async_mode:
        if _event_loop_running():
            from . import asyncio

            async def _task():
                _arm_runtime_async_refresh()
                return await async_main()

            return asyncio.create_task(_task())
        return run(async_main)
    return sync_main()
