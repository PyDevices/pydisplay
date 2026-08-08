# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""asyncio-backed Timer with machine.Timer-compatible API."""

import sys

from ._asyncio_loader import load_asyncio, loop_running
from ._core import _TimerCore


def _require_asyncio():
    aio = load_asyncio()
    if aio is None:
        raise ImportError("AsyncTimer requires asyncio, uasyncio, or _asyncio")
    return aio


def _may_arm_async_timer():
    """True when :meth:`AsyncTimer.init` is allowed to create a task.

    Browser hosts own the loop for the whole program (including import).
    Everywhere else use :func:`loop_running` — not ``get_running_loop`` /
    ``get_event_loop``, which mislead on MicroPython and CircuitPython.
    """
    if sys.platform in ("emscripten", "webassembly"):
        return True
    return loop_running()


class AsyncTimer(_TimerCore):
    """``asyncio``-backed timer with the same API as ``machine.Timer`` / :class:`Timer`.

    Use when ``runtime.timer_async`` is True (PyScript, Jupyter, desktop async).
    :meth:`init` requires a running event loop — prefer constructing at import
    time and calling :meth:`init` (or passing kwargs) only after the loop starts,
    or let ``eventsys.Runtime`` defer arming via ``arm_async_refresh``.

    Inherited: :attr:`ONE_SHOT`, :attr:`PERIODIC`, :meth:`init`, :meth:`deinit`.
    """

    def __init__(self, id=-1, **kwargs):
        """Create an async timer, optionally calling :meth:`init` when kwargs are given.

        Args:
            id: Timer id (kept for API parity; async tasks are not hardware-bound).
            **kwargs: Forwarded to :meth:`init` when non-empty.

        Raises:
            ImportError: No ``asyncio`` / ``uasyncio`` available.
            RuntimeError: :meth:`init` called with no running event loop.
        """
        self._running = False
        self._task = None
        super().__init__(id, **kwargs)

    def _wait_idle(self):
        pass

    def _arm(self):
        aio = _require_asyncio()
        if not _may_arm_async_timer():
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
                self._deliver()
                if self._mode == self.ONE_SHOT or not self._armed:
                    self._running = False
                    break
        except cancelled:
            pass
        finally:
            self._busy = False
