# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Select the platform sync Timer implementation (internal)."""

import sys

Timer = None

try:
    from machine import Timer as _MachineTimer

    Timer = _MachineTimer
except ImportError:
    if sys.implementation.name == "micropython" and sys.platform == "win32":
        from ._backends.polling import Timer
    elif sys.platform == "win32":
        try:
            from ._backends.win32 import Timer
        except ImportError:
            pass
    if (Timer is None and sys.implementation.name == "micropython") or (
        sys.implementation.name == "cpython" and Timer is None
    ):
        try:
            from ._backends.librt import Timer
        except ImportError:
            try:
                from ._backends.threading import Timer
            except ImportError:
                from ._backends.polling import Timer
    elif sys.implementation.name == "circuitpython" and Timer is None:
        try:
            from ._backends.threading import Timer
        except ImportError:
            from ._backends.polling import Timer

if Timer is None:
    raise ImportError("multimer: no Timer backend available on this platform")
