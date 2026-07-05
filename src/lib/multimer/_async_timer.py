# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""asyncio-backed Timer with machine.Timer-compatible API."""

from ._asyncio_loader import load_asyncio
from ._core import _TimerCore


def _require_asyncio():
    aio = load_asyncio()
    if aio is None:
        raise ImportError("AsyncTimer requires asyncio, uasyncio, or _asyncio")
    return aio


def _loop_running(aio):
    if hasattr(aio, "get_running_loop"):
        try:
            aio.get_running_loop()
            return True
        except RuntimeError:
            return False
    try:
        aio.get_event_loop()
        return True
    except (AttributeError, RuntimeError):
        return False


class AsyncTimer(_TimerCore):
    def __init__(self, id=-1, /, **kwargs):
        self._running = False
        self._task = None
        super().__init__(id, **kwargs)

    def _wait_idle(self):
        pass

    def _arm(self):
        aio = _require_asyncio()
        if not _loop_running(aio):
            raise RuntimeError("AsyncTimer.init requires a running event loop")
        self._running = True
        self._task = aio.create_task(self._loop())

    def _disarm(self):
        self._running = False
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()

    async def _loop(self):
        aio = _require_asyncio()
        cancelled = aio.CancelledError
        sleep = getattr(aio, "sleep_ms", None)
        try:
            while self._running:
                if sleep is not None:
                    await sleep(self._period_ms)
                else:
                    await aio.sleep(self._period_ms / 1000)
                if not self._running:
                    break
                self._busy = True
                try:
                    self._invoke_callback(self)
                finally:
                    self._busy = False
                if self._mode == self.ONE_SHOT:
                    self._running = False
                    self._armed = False
                    break
        except cancelled:
            pass
        finally:
            self._busy = False
