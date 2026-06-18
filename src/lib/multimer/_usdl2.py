# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Deprecated: CircuitPython unix multimer uses ``_aio.Timer`` instead.

The compiled ``usdl2`` module exposes ``add_timer`` / ``remove_timer``, but those
callbacks are delivered through ``mp_sched_schedule`` on the main thread.  The
unix REPL blocks on stdin and does not reliably drain that queue while idle at
``>>>``.  Calling Python from the SDL timer thread directly is unsafe on
CircuitPython unix (no GIL).

``displaysys.sdldisplay`` still uses ``usdl2`` for windows, rendering, and
events; only periodic software timers go through ``_aio``.
"""

from ._aio import Timer

__all__ = ["Timer"]
