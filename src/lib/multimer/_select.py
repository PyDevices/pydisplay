# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Select the platform sync Timer implementation (internal)."""

import sys

Timer = None
_sleep_ms = None
_drain = None


def _set_backend(module):
    global Timer, _sleep_ms, _drain
    Timer = module.Timer
    _sleep_ms = getattr(module, "_backend_sleep_ms", None)
    _drain = getattr(module, "_backend_drain", None)


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


if not _async_only_runtime():
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
                from machine import Timer
            except ImportError:
                try:
                    from ._backends import threading

                    _set_backend(threading)
                except ImportError:
                    pass
    if Timer is None:
        try:
            from machine import Timer
        except ImportError:
            try:
                from ._backends import threading

                _set_backend(threading)
            except ImportError:
                try:
                    from ._backends import sdl2

                    _set_backend(sdl2)
                except ImportError:
                    pass
