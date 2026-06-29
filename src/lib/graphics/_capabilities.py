# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Platform capability registry for graphics."""

import sys

_DIALECT = sys.implementation.name

_FORMAT_NAMES = (
    "MONO_VLSB",
    "MONO_HLSB",
    "MONO_HMSB",
    "RGB565",
    "GS2_HMSB",
    "GS4_HMSB",
    "GS8",
)

_CAPS = {
    "framebuf": "pure_python",
    "dialect": _DIALECT,
    "formats": list(_FORMAT_NAMES),
    "image_io": {
        "load": ["pbm", "pgm", "bmp"],
        "save": ["pbm", "pgm", "bmp"],
    },
}


def init_capabilities(*, framebuf_backend, formats=None):
    """Record the selected framebuf backend and supported formats."""
    _CAPS["framebuf"] = framebuf_backend
    _CAPS["dialect"] = _DIALECT
    if formats is not None:
        _CAPS["formats"] = list(formats)


def capabilities():
    """Return a snapshot of platform graphics capabilities."""
    return dict(_CAPS)


def framebuf_backend():
    """Return ``native`` or ``pure_python``."""
    return _CAPS["framebuf"]
