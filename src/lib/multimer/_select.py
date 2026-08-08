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
# backends (SDL2, threading, polling) leave this False.
_uses_signals = False
# Name of the bound backend, one of ``BACKENDS`` (None before one binds).
_backend = None

# Auto-select try order (first ImportError-free bind wins). ``async`` is not
# in this list — it is chosen by :func:`_async_only_runtime` or ``use_backend``.
# ``sdl2`` may be skipped on CPython in :func:`_auto_backends` (see there).
AUTO_BACKENDS = ("machine", "librt", "sdl2", "threading", "polling")

# Every backend name accepted by ``load_backend``. ``machine`` is
# ``machine.Timer``; ``async`` is ``AsyncTimer`` (async-only hosts, and
# selectable elsewhere for async-native apps).
# Concatenation (not (*AUTO_BACKENDS, "async")): MicroPython/CircuitPython
# reject starred expressions in this position.
BACKENDS = AUTO_BACKENDS + ("async",)  # noqa: RUF005

# Forces one backend instead of the automatic choice below. Hosts that cannot
# pass environment variables to a child process (MicroPython Windows under WSL)
# use ``multimer.use_backend()`` instead.
_ENV_OVERRIDE = "MULTIMER_BACKEND"


class _BoundBackend:
    """Shim so machine / AsyncTimer bind through the same globals as modules."""

    def __init__(self, name, timer_cls, *, uses_signals=False, sleep_ms=None, drain=None):
        self.__name__ = name
        self.Timer = timer_cls
        self._uses_signals = uses_signals
        self._backend_sleep_ms = sleep_ms
        self._backend_drain = drain


def _set_backend(module):
    global Timer, _sleep_ms, _drain, _uses_signals, _backend
    Timer = module.Timer
    _sleep_ms = getattr(module, "_backend_sleep_ms", None)
    _drain = getattr(module, "_backend_drain", None)
    _uses_signals = getattr(module, "_uses_signals", False)
    name = getattr(module, "__name__", None)
    if name and "." in name:
        name = name.rsplit(".", 1)[-1]
    _backend = name


def load_backend(name):
    """Bind the backend called ``name`` (one of :data:`BACKENDS`).

    Raises ``ValueError`` for an unknown name and ``ImportError`` when the
    backend is unavailable on this host. Imports stay static so firmware
    manifests still see every backend module.
    """
    if name == "machine":
        from machine import Timer as _MachineTimer

        _set_backend(_BoundBackend("machine", _MachineTimer, uses_signals=True))
    elif name == "async":
        from ._async_timer import AsyncTimer

        _set_backend(_BoundBackend("async", AsyncTimer))
    elif name == "librt":
        from ._backends import librt

        _set_backend(librt)
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


def _try(name):
    """Bind ``name`` when still unbound; ignore ImportError."""
    global Timer
    if Timer is not None:
        return
    try:
        load_backend(name)
    except ImportError:
        pass


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


def _async_only_runtime():
    """True on hosts that have no viable sync timer (PyScript / Jupyter).

    Predicates match desktop ``board_config._host_kind`` so ``Timer`` and
    ``timer_async`` cannot disagree about whether this is an async-only host.
    """
    if sys.platform in ("emscripten", "webassembly"):
        return True
    try:
        import pyscript  # noqa: F401

        return True
    except Exception:
        pass
    try:
        get_ipython()  # noqa: F821
        return True
    except Exception:
        return False


def _pygame_available():
    """True when ``import pygame`` succeeds (pygame-ce or classic)."""
    try:
        import pygame  # noqa: F401

        return True
    except ImportError:
        return False


def _auto_backends():
    """:data:`AUTO_BACKENDS` with host-specific auto skips.

    On CPython, skip auto ``sdl2`` when pygame is importable: that matches
    ``AutoDisplay`` (pygame → ``PGDisplay``), and usdl2 timers plus pygame's
    separate SDL deadlock. Without pygame, CPython may auto-select ``sdl2``
    for ``SDLDisplay`` / usdl2. MicroPython and CircuitPython never skip
    ``sdl2`` here. Explicit ``use_backend`` / ``MULTIMER_BACKEND`` still list
    ``sdl2`` in :data:`BACKENDS`.
    """
    impl = getattr(sys.implementation, "name", "")
    skip_sdl2 = impl == "cpython" and _pygame_available()
    out = []
    for name in AUTO_BACKENDS:
        if name == "sdl2" and skip_sdl2:
            continue
        out.append(name)
    return out


def backends_available():
    """Names from :data:`BACKENDS` that :func:`load_backend` can import here.

    Probes without changing the active backend. Useful for harnesses that skip
    unavailable overrides instead of failing the run.
    """
    global Timer, _sleep_ms, _drain, _uses_signals, _backend
    saved = (Timer, _sleep_ms, _drain, _uses_signals, _backend)
    found = []
    try:
        for name in BACKENDS:
            try:
                load_backend(name)
            except ImportError:
                continue
            found.append(name)
    finally:
        Timer, _sleep_ms, _drain, _uses_signals, _backend = saved
    return tuple(found)


_override = _forced_backend()
if _override is not None:
    # An override that cannot bind is a configuration error: raise instead of
    # falling back, so a mis-set name never masquerades as the platform choice.
    load_backend(_override)
elif _async_only_runtime():
    # PyScript / Jupyter have no sync timer backend. Expose AsyncTimer as Timer so
    # ``from multimer import Timer`` matches the canonical app idiom on every host.
    load_backend("async")
else:
    _tried = _auto_backends()
    for _name in _tried:
        _try(_name)
    if Timer is None:
        raise ImportError(
            "multimer: no timer backend available (tried {})".format(", ".join(_tried))
        )
