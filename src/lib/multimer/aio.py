# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
asyncio/uasyncio Timer for multimer.

Opt-in module — not wired into the package-level ``multimer.Timer``. Use it when
the whole app runs under asyncio/uasyncio (e.g. PyScript, async ports, or
CircuitPython with the asyncio library installed). It tries ``uasyncio`` first,
then falls back to ``asyncio``.

This module is self-contained: the public API is ``Timer`` (an asyncio software
timer with the same ``machine.Timer``-style API as the rest of multimer) plus
optional helpers ``run``, ``run_queued``, ``run_forever``, and ``dual_main``.

Quick start (helpers are optional)::

    from multimer.aio import Timer, run_queued, run, run_forever, dual_main

    async def main():
        t = Timer()
        # init() must be called while the event loop is already running
        t.init(mode=Timer.PERIODIC, period=33, callback=cb)
        while True:
            do_periodic_work()
            await run_queued()  # or await asyncio.sleep(0)

    run(main)  # or asyncio.run(main())

Notes:

- ``Timer.init()`` must run while the event loop is already running; it raises
  ``RuntimeError`` otherwise.  Callbacks run on the event-loop thread.
- ``run(main)`` runs an async ``main`` coroutine function to completion with
  ``asyncio.run`` (or ``run_until_complete``); on a host that already drives a
  loop (Jupyter, PyScript) it schedules ``main`` as a background task instead.
- ``run_queued`` and ``run`` are convenience wrappers only.  Any ``await`` that
  yields to the event loop is sufficient for timer callbacks to fire, so a loop
  that already awaits something can drop ``run_queued`` entirely.
- ``aio.run_queued()`` (async) is unrelated to the sync package-level
  ``multimer.run_queued()`` used by the threading/SDL backends.
"""

try:
    import uasyncio as asyncio
except ImportError:
    try:
        import asyncio
    except ImportError:
        raise ImportError("multimer.aio requires asyncio or uasyncio") from None

try:
    import pyscript
except ImportError:
    pyscript = None

if not hasattr(asyncio, "create_task"):
    raise ImportError("multimer.aio requires asyncio with create_task")

from ._timerbase import _TimerBase


async def _sleep_ms(ms):
    if hasattr(asyncio, "sleep_ms"):
        await asyncio.sleep_ms(ms)
    else:
        await asyncio.sleep(ms / 1000)


async def run_queued():
    """Yield to the event loop so asyncio timer tasks can run.

    Optional helper — equivalent to ``await asyncio.sleep(0)`` (or ``sleep_ms(0)``).
    Not related to sync ``multimer.run_queued()`` from the top-level package.
    """
    await _sleep_ms(0)


async def run_forever(poll=None, *, delay_ms=10):
    """Run the standard asyncio main loop until interrupted.

    Each iteration yields with ``run_queued()``, optionally runs ``poll()`` (awaiting
    if it returns a coroutine), then sleeps for ``delay_ms`` milliseconds.

    Args:
        poll: Optional callable invoked once per iteration after ``run_queued()``.
        delay_ms: Sleep between iterations in milliseconds.
    """
    while True:
        await run_queued()
        if poll is not None:
            result = poll()
            if hasattr(result, "__await__"):
                await result
        await _sleep_ms(delay_ms)


# Strong references to background tasks scheduled by run() on an already-running
# loop.  asyncio only holds weak references to tasks, so without this a
# fire-and-forget task could be garbage collected mid-run.
_background_tasks = set()


def _is_cancelled(exc):
    cancelled = getattr(asyncio, "CancelledError", None)
    return cancelled is not None and isinstance(exc, cancelled)


async def _logged_main(main):
    try:
        return await main()
    except Exception as e:
        if _is_cancelled(e):
            raise
        print("Task failed:", e)
        # PyScript has no task exception handler; re-raising only spams the console.
        if pyscript is None:
            raise


def _task_done(task):
    _background_tasks.discard(task)


def _schedule_background_task(loop, main):
    task = loop.create_task(_logged_main(main))
    _background_tasks.add(task)
    if hasattr(task, "add_done_callback"):
        task.add_done_callback(_task_done)
    return task


def run(main):
    """Run an async main coroutine function under asyncio/uasyncio.

    On a host that already drives an event loop (Jupyter Notebook, PyScript),
    schedule ``main`` on the running loop and return the ``Task`` without
    blocking — ``asyncio.run`` cannot be called re-entrantly there.  Otherwise
    run ``main`` to completion with ``asyncio.run`` (or ``run_until_complete``).
    """
    loop = None
    if hasattr(asyncio, "get_running_loop"):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
    # CPython / Jupyter: schedule only when the loop is actually running.
    is_running = getattr(loop, "is_running", None) if loop is not None else None
    if loop is not None and callable(is_running) and is_running():
        return _schedule_background_task(loop, main)
    # PyScript: mp-script click handlers are synchronous even though the host
    # drives asyncio — get_running_loop() is often unset here, but the global
    # event loop is already active, so schedule and return.
    if pyscript is not None:
        loop = asyncio.get_event_loop()
        return _schedule_background_task(loop, main)
    if hasattr(asyncio, "run"):
        return asyncio.run(main())
    return asyncio.get_event_loop().run_until_complete(main())


def dual_main(sync_main, async_main, *, async_mode=False):
    """Run ``sync_main()`` or schedule ``async_main()`` under asyncio.

    Args:
        sync_main: Callable for the blocking / ``run_queued`` main loop.
        async_main: Async coroutine function for the asyncio main loop.
        async_mode: When ``True``, call ``run(async_main)``; otherwise ``sync_main()``.
    """
    if async_mode:
        run(async_main)
    else:
        sync_main()


class Timer(_TimerBase):
    """asyncio/uasyncio software Timer."""

    REQUIRES_RUN_QUEUED = False

    def __init__(self, id=-1, **kwargs):
        self._running = False
        self._task = None
        super().__init__(id, **kwargs)

    def _start(self):
        if hasattr(asyncio, "get_running_loop"):
            try:
                asyncio.get_running_loop()
            except RuntimeError as err:
                raise RuntimeError("aio.Timer.init requires a running event loop") from err
        else:
            try:
                asyncio.get_event_loop()
            except (AttributeError, RuntimeError) as err:
                raise RuntimeError("aio.Timer.init requires a running event loop") from err
        self._running = True
        self._task = asyncio.create_task(self._loop())

    def _stop(self):
        self._running = False
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()

    async def _loop(self):
        cancelled = asyncio.CancelledError
        try:
            while self._running:
                await _sleep_ms(self._interval)
                if not self._running:
                    break
                self._busy = True
                try:
                    self._callback(self)
                except Exception:
                    pass
                self._busy = False
                if self._mode == self.ONE_SHOT:
                    self._running = False
                    break
        except cancelled:
            pass
        finally:
            self._busy = False
