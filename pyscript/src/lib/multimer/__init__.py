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
    * signal-delivered sync backends (librt): the no-pump sleep;
    * pump-based sync backends (win32 APC, SDL2, threading): the pumping sleep.
    """
    from . import _select

    if _select._async_only_runtime():
        return _sleep_ms_async
    if _select._signal_delivered:
        return _sleep_ms_signal
    return _sleep_ms_pump


sleep_ms = _select_sleep_ms()


def signal_delivered():
    """True when the active sync backend delivers timer callbacks on its own.

    Signal-delivered backends (librt POSIX-timer signal) fire on the main thread
    during a plain sleep, so at an interactive prompt the timer keeps ticking
    with no pump loop. Pump-based backends (win32 APC, SDL2, threading) and the
    async-only runtimes return False. Public accessor so callers (e.g.
    ``eventsys.Runtime.run_forever``) need not reach into ``multimer._select``.
    """
    from . import _select

    return bool(_select._signal_delivered)


__all__ = [
    "AsyncTimer",
    "Timer",
    "asyncio",
    "monotonic",
    "run_deadline_hook",
    "schedule",
    "set_deadline_hook",
    "signal_delivered",
    "sleep_ms",
    "ticks_add",
    "ticks_diff",
    "ticks_less",
    "ticks_ms",
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
