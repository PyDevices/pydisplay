# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Helpers shared by the multimer, eventsys, graphics, and displaysys tests."""

import contextlib
import io

import _env  # noqa: F401

import graphics


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


class FakeFrameBuffer:
    """A minimal stand-in for a CircuitPython ``FrameBuffer``.

    It exposes the three things ``displaysys.fbdisplay.FBDisplay`` needs:

    - a ``width`` / ``height`` in pixels,
    - the buffer protocol (so ``memoryview(fb)`` aliases its bytes), and
    - a ``refresh()`` method that records how many times it was called.

    The backing store is a flat ``bytearray`` of ``width * height * bpp`` bytes,
    accessible as ``fb.data`` for assertions.
    """

    def __init__(self, width, height, bpp=2):
        self.width = width
        self.height = height
        self.bpp = bpp
        self.data = bytearray(width * height * bpp)
        self.refresh_count = 0

    def __buffer__(self, flags):
        return memoryview(self.data)

    def refresh(self):
        self.refresh_count += 1


class FakeU16FrameBuffer:
    """CircuitPython-style RGB565 framebuffer indexed as uint16 elements.

    ``memoryview(fb)`` has length ``width * height`` (not byte length). Qualia's
    ``DotClockFramebuffer`` looks like this; ``FBDisplay`` must paint via a
    ``cast('B')`` byte view rather than a Python per-pixel loop.
    """

    def __init__(self, width, height):
        import array

        self.width = width
        self.height = height
        self.data = array.array("H", [0] * (width * height))
        self.refresh_count = 0

    def __buffer__(self, flags):
        return memoryview(self.data)

    def refresh(self):
        self.refresh_count += 1


@contextlib.contextmanager
def quiet():
    """Suppress the chatty ``print`` calls emitted while building a display."""
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def make_fbdisplay(width=8, height=4, reverse_bytes_in_word=False):
    """Build an ``FBDisplay`` backed by a :class:`FakeFrameBuffer`.

    Returns ``(display, framebuffer)``.
    """
    from displaysys.fbdisplay import FBDisplay

    fb = FakeFrameBuffer(width, height)
    with quiet():
        display = FBDisplay(fb, reverse_bytes_in_word=reverse_bytes_in_word)
    return display, fb


def make_u16_fbdisplay(width=8, height=4, reverse_bytes_in_word=False):
    """Build an ``FBDisplay`` backed by a uint16-indexed framebuffer."""
    from displaysys.fbdisplay import FBDisplay

    fb = FakeU16FrameBuffer(width, height)
    with quiet():
        display = FBDisplay(fb, reverse_bytes_in_word=reverse_bytes_in_word)
    return display, fb
