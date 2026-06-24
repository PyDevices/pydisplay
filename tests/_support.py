# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Helpers shared by the displaysys tests.

The display drivers print progress to ``stdout`` during construction; the
helpers here keep test output quiet and provide a hardware-free framebuffer so
``FBDisplay`` (and, through it, the ``DisplayDriver`` base class) can be
exercised on plain CPython.
"""

import contextlib
import io

import _env  # noqa: F401


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
        # PEP 688 buffer protocol (CPython >= 3.12) so memoryview() aliases
        # the same bytes the display writes into.
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
