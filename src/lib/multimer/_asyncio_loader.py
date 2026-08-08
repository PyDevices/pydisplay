# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Load asyncio, uasyncio, or the _mpasyncio shim (internal)."""

_asyncio_mod = None


def load_asyncio():
    global _asyncio_mod
    if _asyncio_mod is not None:
        return _asyncio_mod

    # Prefer ``asyncio`` over ``uasyncio``. On modern MicroPython, ``uasyncio`` is
    # a lazy shim whose ``__getattr__`` forwards into ``sys.modules["asyncio"]``.
    # Caching that shim breaks ``install_asyncio_compat``: after the facade
    # replaces the ``asyncio`` name, shim → facade → shim recurses on getattr.
    try:
        import asyncio as aio

        if hasattr(aio, "create_task"):
            _asyncio_mod = aio
            return aio
    except ImportError:
        pass

    try:
        import uasyncio as aio

        if hasattr(aio, "create_task"):
            _asyncio_mod = aio
            return aio
    except ImportError:
        pass

    try:
        import _asyncio  # noqa: F401
    except ImportError:
        return None

    # Fallback for incomplete builds (e.g. micropython.exe without frozen asyncio).
    # Production desktop firmware should freeze extmod/asyncio — see
    # docs/platforms/micropython.md.
    aio = __import__("multimer._mpasyncio", None, None, ("_mpasyncio",))

    _asyncio_mod = aio
    return aio


def loop_running():
    """True when a coroutine of a running event loop is currently executing.

    ``current_task()`` is the only probe that answers this correctly on every
    supported runtime, so prefer it whenever the implementation has it:

    * uasyncio (MicroPython) has no ``get_running_loop`` at all, so testing for
      that name reports "no loop" even from inside a task;
    * CircuitPython's ``get_running_loop()`` succeeds even when no loop is
      running, reporting a loop that is not there;
    * ``get_event_loop()`` creates or returns a loop on every implementation, so
      it can never answer this question.
    """
    aio = load_asyncio()
    if aio is None:
        return False
    current_task = getattr(aio, "current_task", None)
    if current_task is not None:
        try:
            return current_task() is not None
        except RuntimeError:
            return False
    get_running_loop = getattr(aio, "get_running_loop", None)
    if get_running_loop is not None:
        try:
            get_running_loop()
            return True
        except RuntimeError:
            return False
    return False
