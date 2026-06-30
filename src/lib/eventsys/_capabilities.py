# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Platform capability registry for eventsys."""

import sys

_DIALECT = sys.implementation.name

_CAPS = {
    "dialect": _DIALECT,
    "devices": ["broker", "queue", "touch", "encoder", "keypad", "joystick"],
    "joystick": True,
}


def capabilities():
    """Return a snapshot of eventsys capabilities."""
    return dict(_CAPS)
