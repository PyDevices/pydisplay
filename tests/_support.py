# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Helpers shared by the multimer, eventsys, and graphics tests."""

import time

import _env  # noqa: F401

import graphics
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


def make_fb(format=graphics.RGB565, w=16, h=16):
    """Return a fresh :class:`graphics.FrameBuffer` of the given format.

    The backing buffer is always allocated at ``w * h * 2`` bytes, which is
    large enough for every supported color depth (1-16 bits per pixel), so the
    same helper works for mono, grayscale and RGB565 framebuffers.
    """
    buffer = bytearray(w * h * 2)
    return graphics.FrameBuffer(buffer, w, h, format)


def set_pixels(fb):
    """Return the set of ``(x, y)`` coordinates whose pixel value is non-zero."""
    return {(x, y) for y in range(fb.height) for x in range(fb.width) if fb.pixel(x, y)}


def count_set(fb):
    """Return how many pixels in ``fb`` have a non-zero value."""
    return len(set_pixels(fb))
