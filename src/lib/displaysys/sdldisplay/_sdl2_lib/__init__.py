# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
This module provides the SDL2 library implementation for MicroPython, CircuitPython,
and CPython.

The module checks the implementation name and imports the appropriate backend.
"""

from sys import implementation

if implementation.name == "micropython":
    from ._micropython import *  # noqa: F403
elif implementation.name == "circuitpython":
    from ._circuitpython import *  # noqa: F403
else:
    from ._cpython import *  # noqa: F403
