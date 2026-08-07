# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Select the platform sync Timer implementation (internal)."""

import sys

Timer = None
_sleep_ms = None
_drain = None
# True when the active backend delivers timer callbacks without a sleep/pump
# loop (librt POSIX-timer signals, or MicroPython ``machine.Timer``). Pump-based
# backends (win32 APC, SDL2, the threading fallback) leave this False.
_uses_signals = False
# Name of the bound backend, one of ``BACKENDS`` (None before one binds).
_backend = None

# Every backend name accepted by ``load_backend``. ``machine`` is
# ``machine.Timer``; ``async`` is ``AsyncTimer`` (the only choice on hosts
# without a sync timer, and selectable elsewhere for async-native apps).
BACKENDS = ("librt", "machine", "win32", "sdl2", "threading", "polling", "async")

# Forces one backend instead of the automatic choice below. Hosts that cannot
# pass environment variables to a child process (MicroPython Windows under WSL)
# use ``multimer.use_backend()`` instead.
_ENV_OVERRIDE = "MULTIMER_BACKEND"


def _set_backend(module):
    global Timer, _sleep_ms, _drain, _uses_signals, _backend
    Timer = module.Timer
    _sleep_ms = getattr(module, "_backend_sleep_ms", None)
    _drain = getattr(module, "_backend_drain", None)
    _uses_signals = getattr(module, "_uses_signals", False)
    _backend = module.__name__.rsplit(".", 1)[-1]


def _use_machine_timer():
    """Bind MicroPython/CircuitPython ``machine.Timer`` (self-driving)."""
    global Timer, _uses_signals, _backend
    from machine import Timer as _MachineTimer

    Timer = _MachineTimer
    _uses_signals = True
    _backend = "machine"


def _use_async_timer():
    """Bind :class:`AsyncTimer` as ``Timer`` (no sync timer on this host)."""
    global Timer, _sleep_ms, _drain, _uses_signals, _backend
    from ._async_timer import AsyncTimer

    Timer = AsyncTimer
    _sleep_ms = None
    _drain = None
    _uses_signals = False
    _backend = "async"


def load_backend(name):
    """Bind the backend called ``name`` (one of :data:`BACKENDS`).

    Raises ``ValueError`` for an unknown name and ``ImportError`` when the
    backend is unavailable on this host. Imports stay static so firmware
    manifests still see every backend module.
    """
    if name == "machine":
        _use_machine_timer()
    elif name == "async":
        _use_async_timer()
    elif name == "librt":
        from ._backends import librt

        _set_backend(librt)
    elif name == "win32":
        from ._backends import win32

        _set_backend(win32)
    elif name == "sdl2":
        from ._backends import sdl2

        _set_backend(sdl2)
    elif name == "threading":
        from ._backends import threading

        _set_backend(threading)
    elif name == "polling":
        from ._backends import polling

        _set_backend(polling)
    else:
        raise ValueError(f"unknown multimer backend: {name!r} (expected one of {BACKENDS})")


def _forced_backend():
    """Read :data:`_ENV_OVERRIDE`, or None when unset / unreadable here."""
    import os

    getenv = getattr(os, "getenv", None)
    if getenv is None:
        return None
    try:
        value = getenv(_ENV_OVERRIDE)
    except Exception:
        return None
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _running_in_ipython_kernel():
    import builtins

    get_ipython = getattr(builtins, "get_ipython", None)
    if get_ipython is None:
        return False
    try:
        shell = get_ipython()
    except Exception:
        return False
    return shell is not None and shell.__class__.__name__ == "ZMQInteractiveShell"


def _async_only_runtime():
    return sys.platform in ("emscripten", "webassembly") or _running_in_ipython_kernel()


_override = _forced_backend()
if _override is not None:
    # An override that cannot bind is a configuration error: raise instead of
    # falling back, so a mis-set name never masquerades as the platform choice.
    load_backend(_override)
elif _async_only_runtime():
    # PyScript / Jupyter have no sync timer backend. Expose AsyncTimer as Timer so
    # ``from multimer import Timer`` matches the canonical app idiom on every host.
    _use_async_timer()
else:
    if sys.platform == "win32":
        # CPython 3.14: win32 QueueUserAPC + ctypes trampoline into LVGL/extension
        # code fatals with ``_PyThreadState_Attach: non-NULL old thread state``
        # (seen on touch → indev read_cb). Prefer the threading backend, which
        # only ``schedule()``s from the worker and drains on the main pump.
        # Keep win32 APC for MicroPython Windows and as CPython fallback.
        if getattr(sys.implementation, "name", "") == "cpython":
            try:
                load_backend("threading")
            except ImportError:
                pass
        if Timer is None:
            try:
                load_backend("win32")
            except ImportError:
                pass
    elif sys.platform in ("linux", "unix"):
        try:
            load_backend("librt")
        except ImportError:
            try:
                load_backend("machine")
            except ImportError:
                try:
                    load_backend("threading")
                except ImportError:
                    pass
    if Timer is None:
        try:
            load_backend("machine")
        except ImportError:
            try:
                load_backend("threading")
            except ImportError:
                try:
                    load_backend("sdl2")
                except ImportError:
                    try:
                        load_backend("polling")
                    except ImportError:
                        # CircuitPython: no machine.Timer; async-only Timer API.
                        if getattr(sys.implementation, "name", "") == "circuitpython":
                            _use_async_timer()
