# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Helpers shared by the graphics tests."""

import _env  # noqa: F401

import graphics


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
