# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
multimer — cross-platform machine.Timer for CPython, MicroPython, and CircuitPython.
"""

from ._async_timer import AsyncTimer
from ._schedule import schedule
from ._ticks import (
    monotonic,
    run_deadline_hook,
    set_deadline_hook,
    sleep_ms,
    ticks_add,
    ticks_diff,
    ticks_less,
    ticks_ms,
)
from ._timer import Timer

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
]


def _load_loop_submodule():
    # MicroPython: ``from . import loop`` inside __getattr__ re-enters __getattr__('loop').
    return __import__(__name__ + ".loop", None, None, ["*"])


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
    if name == "loop":
        return _load_loop_submodule()
    if name in ("run", "run_forever", "run_forever_async", "dual_main"):
        return getattr(_load_loop_submodule(), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
