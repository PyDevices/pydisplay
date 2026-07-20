# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
multimer — cross-platform machine.Timer for CPython, MicroPython, and CircuitPython.
"""

from ._async_timer import AsyncTimer
from ._schedule import schedule
from ._ticks import (
    _sleep_ms_async,
    _sleep_ms_pump,
    _sleep_ms_signal,
    monotonic,
    run_deadline_hook,
    set_deadline_hook,
    ticks_add,
    ticks_diff,
    ticks_less,
    ticks_ms,
)
from ._timer import Timer


def _select_sleep_ms():
    """Bind ``sleep_ms`` to the variant matching the active timer backend.

    * async-only runtimes (PyScript/Jupyter): the awaitable async sleep;
    * signal-based sync backends (librt): the no-pump sleep;
    * pump-based sync backends (win32 APC, SDL2, threading): the pumping sleep.
    """
    from . import _select

    if _select._async_only_runtime():
        return _sleep_ms_async
    if _select._uses_signals:
        return _sleep_ms_signal
    return _sleep_ms_pump


sleep_ms = _select_sleep_ms()


def uses_signals():
    """True when the active sync backend delivers timers without a sleep pump.

    Covers librt POSIX-timer signals and MicroPython ``machine.Timer``: callbacks
    keep firing at an interactive prompt with no ``run_forever`` keep-alive loop.
    Pump-based backends (win32 APC, SDL2, threading) and async-only runtimes
    return False. Public accessor so callers (e.g. ``eventsys.Runtime.run_forever``)
    need not reach into ``multimer._select``.
    """
    from . import _select

    return bool(_select._uses_signals)


__all__ = [
    "AsyncTimer",
    "Timer",
    "asyncio",
    "monotonic",
    "run_deadline_hook",
    "schedule",
    "set_deadline_hook",
    "sleep_ms",
    "ticks_add",
    "ticks_diff",
    "ticks_less",
    "ticks_ms",
    "uses_signals",
]


def __getattr__(name):
    if name == "asyncio":
        from ._asyncio_loader import load_asyncio

        mod = load_asyncio()
        if mod is None:
            raise ImportError(
                "multimer: asyncio not available — freeze extmod/asyncio in the "
                "firmware manifest (see docs/building.md)"
            )
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
