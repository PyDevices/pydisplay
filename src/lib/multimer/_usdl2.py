# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Deprecated: CircuitPython unix multimer uses ``_aio.Timer`` instead.

``displaysys.sdldisplay`` uses ``usdl2`` for windows, rendering, and events;
periodic software timers use ``_aio`` (thread-based).
"""

from ._aio import Timer

__all__ = ["Timer"]
