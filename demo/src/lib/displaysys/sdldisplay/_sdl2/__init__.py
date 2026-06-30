# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
This module provides the SDL2 library implementation for MicroPython, CircuitPython,
and CPython.

Import order: native ``usdl2`` module, then MicroPython ``._ffi``, then ``._ctypes``.
"""

from sys import implementation

try:
    from usdl2 import *  # noqa: F403
except ImportError:
    if implementation.name == "micropython":
        try:
            from ._ffi import *  # noqa: F403
        except ImportError:
            from ._ctypes import *  # noqa: F403
    else:
        from ._ctypes import *  # noqa: F403
