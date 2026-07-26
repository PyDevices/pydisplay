# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts pydisplay packages on ``sys.path``.

Puts ``src/lib`` (displaysys, eventsys, multimer) and sibling ``graphics/lib``
on ``sys.path`` without installing anything. Import it before importing those
packages in any test module::

    import _env  # noqa: F401
    import multimer
    import eventsys
    import graphics
    import displaysys
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_LIB = os.path.join(_REPO_ROOT, "src", "lib")
_SRC_ADDONS = os.path.join(_REPO_ROOT, "src", "add_ons")
_GRAPHICS_LIB = os.path.abspath(os.path.join(_REPO_ROOT, "..", "graphics", "lib"))

if _SRC_LIB not in sys.path:
    sys.path.insert(0, _SRC_LIB)
if _SRC_ADDONS not in sys.path:
    sys.path.insert(0, _SRC_ADDONS)
if os.path.isdir(_GRAPHICS_LIB) and _GRAPHICS_LIB not in sys.path:
    sys.path.insert(0, _GRAPHICS_LIB)
