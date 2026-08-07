# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
multimer — cross-platform ``machine.Timer`` for CPython, MicroPython, and CircuitPython.

Public surface::

    from multimer import Timer, AsyncTimer, schedule, sleep_ms, ticks_ms
    from multimer import ticks_add, ticks_diff, ticks_less, monotonic, uses_signals
    from multimer import backend_name, backends, use_backend

``Timer`` selects a platform backend (librt, win32 APC, SDL2, threading, or
``machine.Timer``). On async-only hosts (PyScript / Jupyter), ``Timer`` is an
alias of :class:`AsyncTimer`. Soft callbacks (``hard=False``) use
:func:`schedule`; on signal backends that already deliver on main, soft does
not postpone the callback (coalesce/gap still apply).

Set ``MULTIMER_BACKEND`` or call :func:`use_backend` to pick a backend
explicitly; :func:`backend_name` reports the active one. See also:
https://pydisplay.readthedocs.io/en/latest/concepts/multimer/
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

    * ``AsyncTimer`` as ``Timer`` (PyScript/Jupyter, or ``use_backend("async")``):
      the awaitable async sleep;
    * signal-based sync backends (librt, ``machine.Timer``): the no-pump sleep;
    * pump-based sync backends (win32 APC, SDL2, threading, polling): the
      pumping sleep.
    """
    from . import _select

    if _select._backend == "async":
        return _sleep_ms_async
    if _select._uses_signals:
        return _sleep_ms_signal
    return _sleep_ms_pump


sleep_ms = _select_sleep_ms()


def backend_name():
    """Name of the active timer backend, one of :func:`backends`."""
    from . import _select

    return _select._backend


def backends():
    """Every backend name accepted by :func:`use_backend`."""
    from . import _select

    return _select.BACKENDS


def use_backend(name):
    """Rebind ``Timer`` and ``sleep_ms`` to the backend called ``name``.

    Complements the automatic choice made at import and the ``MULTIMER_BACKEND``
    environment variable, for hosts that cannot pass environment variables to a
    child process (MicroPython Windows launched from WSL) and for tests that
    exercise one backend per run. Call it before creating any timer.

    Raises ``ValueError`` for an unknown name and ``ImportError`` when the
    backend is unavailable on this host. Returns the active backend name.
    """
    global Timer, sleep_ms
    from . import _select, _timer

    _select.load_backend(name)
    Timer = _select.Timer
    _timer.Timer = _select.Timer
    sleep_ms = _select_sleep_ms()
    return _select._backend


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


def install_asyncio_compat():
    """Expose the host-loop-safe facade as both asyncio module names.

    This is opt-in for applications which must run unchanged code that invokes
    ``asyncio.run`` even when a host such as PyScript already owns the loop.
    ``multimer.asyncio`` continues to return the unmodified backend.
    """
    import sys

    compat = __import__("multimer.asyncio_compat", None, None, ("asyncio_compat",))
    compat.backend()  # Resolve the real backend before replacing names.
    sys.modules["asyncio"] = compat
    sys.modules["uasyncio"] = compat
    return compat


__all__ = [
    "AsyncTimer",
    "Timer",
    "asyncio",
    "backend_name",
    "backends",
    "install_asyncio_compat",
    "monotonic",
    "run_deadline_hook",
    "schedule",
    "set_deadline_hook",
    "sleep_ms",
    "ticks_add",
    "ticks_diff",
    "ticks_less",
    "ticks_ms",
    "use_backend",
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
