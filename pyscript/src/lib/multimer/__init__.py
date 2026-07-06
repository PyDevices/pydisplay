# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
multimer — cross-platform machine.Timer for CPython, MicroPython, and CircuitPython.
"""

from ._async_timer import AsyncTimer
from ._schedule import schedule
from ._ticks import sleep_ms, ticks_add, ticks_diff, ticks_less, ticks_ms
from ._timer import Timer

__all__ = [
    "AsyncTimer",
    "Timer",
    "asyncio",
    "schedule",
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
