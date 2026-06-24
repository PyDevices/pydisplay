# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
asyncio/uasyncio Timer for multimer.

Opt-in module — not wired into ``multimer.Timer``. Use when the app runs under
asyncio/uasyncio. See ``docs/concepts/multimer.md`` for full documentation.

Quick start (helpers are optional)::

    from multimer.aio import Timer, run_queued, run

    async def main():
        t = Timer()
        t.init(mode=Timer.PERIODIC, period=33, callback=cb)
        while True:
            broker.poll()
            display.show()
            await run_queued()  # or await asyncio.sleep(0)

    run(main)  # or asyncio.run(main())

``run_queued`` and ``run`` are convenience wrappers only. Any ``await`` that
yields to the event loop is sufficient for timer callbacks to fire.
"""

try:
    import uasyncio as asyncio
except ImportError:
    try:
        import asyncio
    except ImportError:
        raise ImportError("multimer.aio requires asyncio or uasyncio") from None

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


# Strong references to background tasks scheduled by run() on an already-running
# loop.  asyncio only holds weak references to tasks, so without this a
# fire-and-forget task could be garbage collected mid-run.
_background_tasks = set()


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
    if loop is not None:
        task = loop.create_task(main())
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        return task
    if hasattr(asyncio, "run"):
        return asyncio.run(main())
    return asyncio.get_event_loop().run_until_complete(main())


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
