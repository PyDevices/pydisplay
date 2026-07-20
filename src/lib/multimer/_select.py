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


def _set_backend(module):
    global Timer, _sleep_ms, _drain, _uses_signals
    Timer = module.Timer
    _sleep_ms = getattr(module, "_backend_sleep_ms", None)
    _drain = getattr(module, "_backend_drain", None)
    _uses_signals = getattr(module, "_uses_signals", False)


def _use_machine_timer():
    """Bind MicroPython/CircuitPython ``machine.Timer`` (self-driving)."""
    global Timer, _uses_signals
    from machine import Timer as _MachineTimer

    Timer = _MachineTimer
    _uses_signals = True


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


if _async_only_runtime():
    # PyScript / Jupyter have no sync timer backend. Expose AsyncTimer as Timer so
    # ``from multimer import Timer`` matches the canonical app idiom on every host.
    from ._async_timer import AsyncTimer

    Timer = AsyncTimer
else:
    if sys.platform == "win32":
        try:
            from ._backends import win32

            _set_backend(win32)
        except ImportError:
            pass
    elif sys.platform in ("linux", "unix"):
        try:
            from ._backends import librt

            _set_backend(librt)
        except ImportError:
            try:
                _use_machine_timer()
            except ImportError:
                try:
                    from ._backends import threading

                    _set_backend(threading)
                except ImportError:
                    pass
    if Timer is None:
        try:
            _use_machine_timer()
        except ImportError:
            try:
                from ._backends import threading

                _set_backend(threading)
            except ImportError:
                try:
                    from ._backends import sdl2

                    _set_backend(sdl2)
                except ImportError:
                    try:
                        from ._backends import polling

                        _set_backend(polling)
                    except ImportError:
                        # CircuitPython: no machine.Timer; async-only Timer API.
                        if getattr(sys.implementation, "name", "") == "circuitpython":
                            from ._async_timer import AsyncTimer

                            Timer = AsyncTimer
