# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
This module provides the SDL2 library implementation for MicroPython, CircuitPython,
and CPython.

The module checks the implementation name and imports the appropriate backend.
"""

from sys import implementation

if implementation.name in ("micropython", "circuitpython"):
    try:
        import usdl2  # noqa: F401

        from ._usdl2 import *  # noqa: F403
    except ImportError:
        if implementation.name == "micropython":
            from ._ffi import *  # noqa: F403
        else:
            raise
else:
    from ._cpython import *  # noqa: F403
