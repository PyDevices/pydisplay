# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Select the platform sync Timer implementation (internal)."""

import sys

Timer = None


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
            from ._backends.win32 import Timer
        except ImportError:
            pass
    elif sys.platform in ("linux", "unix"):
        try:
            from ._backends.librt import Timer
        except ImportError:
            pass
    else:
        try:
            from machine import Timer
        except ImportError:
            pass
