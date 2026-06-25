# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Helpers shared by the multimer and eventsys tests."""

import time

import _env  # noqa: F401

import multimer


def pump(duration_s, step_s=0.005):
    """Drive timers for ``duration_s`` seconds.

    Works across every synchronous backend:

    - threading / SDL / polling backends deliver callbacks through the schedule
      queue, which ``multimer.run_queued()`` drains here on the main thread;
    - the POSIX ``_ctypes``/``_ffi`` backends deliver callbacks on the main
      thread during ``time.sleep`` (``run_queued`` is then a harmless no-op).
    """
    end = time.monotonic() + duration_s
    while time.monotonic() < end:
        multimer.run_queued()
        time.sleep(step_s)
    multimer.run_queued()


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
