# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Helpers shared by the eventsys device tests."""

import _env  # noqa: F401


def scripted(*values):
    """Return a zero-arg callable that yields ``values`` one poll at a time.

    Once the scripted values run out, the callable keeps returning the final
    value, which makes it convenient as a device ``read`` callback that should
    settle into a steady state.
    """
    box = {"i": 0, "values": list(values)}

    def read():
        i = box["i"]
        seq = box["values"]
        if i < len(seq):
            box["i"] = i + 1
            return seq[i]
        return seq[-1] if seq else None

    return read


class FakeDisplay:
    """Minimal stand-in for a display driver used by ``TouchDevice``.

    ``TouchDevice`` only needs ``width``/``height``/``rotation`` and a settable
    ``touch_device`` attribute, so this avoids pulling in ``displaysys``.
    """

    def __init__(self, width=320, height=240, rotation=0):
        self.width = width
        self.height = height
        self.rotation = rotation
        self.touch_device = None
