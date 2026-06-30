# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""asyncio/uasyncio Timer and helpers for multimer."""

try:
    import pyscript
except ImportError:
    pyscript = None


def _load_asyncio():
    try:
        import uasyncio as aio

        if hasattr(aio, "create_task"):
            return aio
    except ImportError:
        pass
    try:
        import asyncio as aio

        if hasattr(aio, "create_task"):
            return aio
    except ImportError:
        pass
    try:
        import _asyncio  # noqa: F401
    except ImportError:
        return None
    try:
        from . import _mpasyncio as aio

        return aio
    except ImportError:
        return None


asyncio = _load_asyncio()

from ._timerbase import _TimerBase  # noqa: E402

_background_tasks = set()


def _require_asyncio():
    if asyncio is None:
        raise ImportError("multimer async support requires asyncio or uasyncio with create_task")
    return asyncio


async def sleep_ms(ms):
    """Async sleep in milliseconds. Yields to the event loop."""
    aio = _require_asyncio()
    if hasattr(aio, "sleep_ms"):
        await aio.sleep_ms(ms)
    else:
        await aio.sleep(ms / 1000)


async def run_forever_async(poll=None, *, delay_ms=10):
    """Run the standard asyncio main loop until ``poll()`` returns True or interrupted."""
    while True:
        await sleep_ms(0)
        if poll is not None:
            result = poll()
            if hasattr(result, "__await__"):
                result = await result
            if result is True:
                break
        await sleep_ms(delay_ms)


def _is_cancelled(exc):
    aio = _require_asyncio()
    cancelled = getattr(aio, "CancelledError", None)
    return cancelled is not None and isinstance(exc, cancelled)


async def _logged_main(main):
    try:
        return await main()
    except Exception as e:
        if _is_cancelled(e):
            raise
        print("Task failed:", e)
        if pyscript is None:
            raise


def _task_done(task):
    _background_tasks.discard(task)


def _schedule_background_task(loop, main):
    _require_asyncio()
    task = loop.create_task(_logged_main(main))
    _background_tasks.add(task)
    if hasattr(task, "add_done_callback"):
        task.add_done_callback(_task_done)
    return task


def run(main):
    """Run an async main coroutine function under asyncio/uasyncio."""
    aio = _require_asyncio()
    loop = None
    if hasattr(aio, "get_running_loop"):
        try:
            loop = aio.get_running_loop()
        except RuntimeError:
            loop = None
    is_running = getattr(loop, "is_running", None) if loop is not None else None
    if loop is not None and callable(is_running) and is_running():
        return _schedule_background_task(loop, main)
    if pyscript is not None:
        loop = aio.get_event_loop()
        return _schedule_background_task(loop, main)
    if hasattr(aio, "run"):
        return aio.run(main())
    return aio.get_event_loop().run_until_complete(main())


def dual_main(sync_main, async_main, *, async_mode=False):
    """Run ``sync_main()`` or schedule ``async_main()`` under asyncio."""
    if async_mode:
        run(async_main)
    else:
        sync_main()


class AsyncTimer(_TimerBase):
    """asyncio/uasyncio software Timer with a machine.Timer-compatible API."""

    BACKEND = "asyncio"
    NEEDS_PUMP = False

    def __init__(self, id=-1, **kwargs):
        self._running = False
        self._task = None
        super().__init__(id, **kwargs)

    @property
    def needs_pump(self):
        return False

    def _wait_for_callback(self):
        pass

    def _start(self):
        aio = _require_asyncio()
        if hasattr(aio, "get_running_loop"):
            try:
                aio.get_running_loop()
            except RuntimeError as err:
                raise RuntimeError("AsyncTimer.init requires a running event loop") from err
        else:
            try:
                aio.get_event_loop()
            except (AttributeError, RuntimeError) as err:
                raise RuntimeError("AsyncTimer.init requires a running event loop") from err
        self._running = True
        self._task = aio.create_task(self._loop())

    def _stop(self):
        self._running = False
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()

    async def _loop(self):
        aio = _require_asyncio()
        cancelled = aio.CancelledError
        try:
            while self._running:
                await sleep_ms(self._interval)
                if not self._running:
                    break
                self._busy = True
                try:
                    self._invoke_callback(self)
                finally:
                    self._busy = False
                if self._mode == self.ONE_SHOT:
                    self._running = False
                    break
        except cancelled:
            pass
        finally:
            self._busy = False
