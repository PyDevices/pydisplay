# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Platform capability registry for eventsys."""

import sys

_DIALECT = sys.implementation.name

_CAPS = {
    "dialect": _DIALECT,
    "devices": ["runtime", "host", "pointer", "encoder", "keypad", "joystick"],
    "joystick": True,
}


def capabilities():
    """Return a snapshot of eventsys capabilities."""
    return dict(_CAPS)
