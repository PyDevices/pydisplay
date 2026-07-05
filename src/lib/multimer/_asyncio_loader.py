# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Load asyncio, uasyncio, or the _mpasyncio shim (internal)."""

_asyncio_mod = None


def load_asyncio():
    global _asyncio_mod
    if _asyncio_mod is not None:
        return _asyncio_mod

    try:
        import uasyncio as aio

        if hasattr(aio, "create_task"):
            _asyncio_mod = aio
            return aio
    except ImportError:
        pass

    try:
        import asyncio as aio

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
    # Production desktop firmware should freeze extmod/asyncio — see docs/building.md.
    from . import _mpasyncio as aio

    _asyncio_mod = aio
    return aio
