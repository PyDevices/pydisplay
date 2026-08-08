# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
multimer — cross-platform ``machine.Timer`` for CPython, MicroPython, and CircuitPython.

Public surface::

    from multimer import Timer, AsyncTimer, schedule, sleep_ms, ticks_ms
    from multimer import ticks_add, ticks_diff, ticks_less, monotonic, uses_signals
    from multimer import backend_name, backends, backends_available, use_backend
    from multimer import loop_running, install_asyncio_compat

``Timer`` selects a platform backend at import (``machine`` → ``librt`` →
``sdl2`` → ``threading`` → ``polling``; on CPython, ``sdl2`` is skipped when
pygame is importable). On async-only hosts (PyScript / Jupyter), ``Timer`` is
an alias of :class:`AsyncTimer`. Soft callbacks (``hard=False``) use
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
    * pump-based sync backends (SDL2, threading, polling): the pumping sleep.
    """
    from . import _select

    if _select._backend == "async":
        return _sleep_ms_async
    if _select._uses_signals:
        return _sleep_ms_signal
    return _sleep_ms_pump


sleep_ms = _select_sleep_ms()


def loop_running():
    """True when an asyncio event loop is running *and* executing a coroutine.

    The reliable cross-runtime answer to "may I create an ``AsyncTimer`` now?".
    Callers must not hand-roll this from ``get_running_loop`` / ``get_event_loop``
    — see :func:`multimer._asyncio_loader.loop_running` for why those mislead on
    MicroPython and CircuitPython.
    """
    import sys

    # Browser hosts own the loop for the whole lifetime of the program, including
    # module import, where no task of ours is executing yet.
    if sys.platform in ("emscripten", "webassembly"):
        return True
    from ._asyncio_loader import loop_running as _loop_running

    return _loop_running()


def backend_name():
    """Name of the active timer backend, one of :func:`backends`."""
    from . import _select

    return _select._backend


def backends():
    """Every backend name accepted by :func:`use_backend`."""
    from . import _select

    return _select.BACKENDS


def backends_available():
    """Backend names from :func:`backends` that can import on this host."""
    from . import _select

    return _select.backends_available()


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
    Pump-based backends (SDL2, threading, polling) and async-only runtimes
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

    from . import _asyncio_loader

    # Pin the concrete implementation *before* replacing module names.
    # MicroPython's ``uasyncio`` shim forwards missing attrs into
    # ``sys.modules["asyncio"]``; if that name becomes this facade while the
    # loader/compat still hold the shim, ``getattr`` recurses until the
    # recursion limit (seen via ``color_setup`` + ``timer_async``).
    try:
        import asyncio as real
    except ImportError:
        real = _asyncio_loader.load_asyncio()
    if real is None:
        raise ImportError("multimer.install_asyncio_compat: asyncio is not available")
    if getattr(real, "__name__", "") == "multimer.asyncio_compat":
        sys.modules["asyncio"] = real
        sys.modules["uasyncio"] = real
        return real

    _asyncio_loader._asyncio_mod = real

    compat = __import__("multimer.asyncio_compat", None, None, ("asyncio_compat",))
    compat._backend = real
    sys.modules["asyncio"] = compat
    sys.modules["uasyncio"] = compat
    return compat


__all__ = [
    "AsyncTimer",
    "Timer",
    "asyncio",
    "backend_name",
    "backends",
    "backends_available",
    "install_asyncio_compat",
    "loop_running",
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
                "firmware manifest (see docs/platforms/micropython.md)"
            )
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
