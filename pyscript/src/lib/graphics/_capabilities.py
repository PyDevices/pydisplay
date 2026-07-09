# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Platform capability registry for graphics."""

import sys

_DIALECT = sys.implementation.name
_PYDISPLAY_LIB = True

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
    "implementation": "pydisplay_python",
    "framebuf": "pure_python",
    "dialect": _DIALECT,
    "formats": list(_FORMAT_NAMES),
    "image_io": {
        "load": ["pbm", "pgm", "bmp"],
        "save": ["pbm", "pgm", "bmp"],
    },
    "blit": {
        "framebuf": "pure_python",
        "rect_hook": True,
    },
}


def init_capabilities(*, framebuf_backend, formats=None, implementation=None):
    """Record the selected framebuf backend and supported formats."""
    _CAPS["framebuf"] = framebuf_backend
    _CAPS["dialect"] = _DIALECT
    _CAPS["blit"]["framebuf"] = framebuf_backend
    if formats is not None:
        _CAPS["formats"] = list(formats)
    if implementation is not None:
        _CAPS["implementation"] = implementation


def capabilities():
    """Return a snapshot of platform graphics capabilities."""
    return dict(_CAPS)


def framebuf_backend():
    """Return ``native`` or ``pure_python``."""
    return _CAPS["framebuf"]


def implementation():
    """Return ``native_cmod`` or ``pydisplay_python``."""
    return _CAPS["implementation"]
