# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts pydisplay packages on ``sys.path``.

The tests are self-contained: importing this module makes ``src/lib`` (where
the ``eventsys``, ``graphics``, and ``displaysys`` packages live) and the
sibling ``multimer`` repo importable without installing anything. Import it
before importing those packages in any test module::

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
_MULTIMER_ROOT = os.path.abspath(os.path.join(_REPO_ROOT, "..", "multimer"))

if _SRC_LIB not in sys.path:
    sys.path.insert(0, _SRC_LIB)

if os.path.isdir(os.path.join(_MULTIMER_ROOT, "multimer")) and _MULTIMER_ROOT not in sys.path:
    sys.path.insert(0, _MULTIMER_ROOT)

#: Absolute path to the ``multimer`` package directory (sibling repo).
MULTIMER_DIR = os.path.join(_MULTIMER_ROOT, "multimer")

#: Absolute path to the ``eventsys`` package directory, handy for tests that
#: want to copy it somewhere isolated.
EVENTSYS_DIR = os.path.join(_SRC_LIB, "eventsys")

#: Absolute path to the ``graphics`` package directory, handy for tests that
#: want to copy it somewhere isolated.
GRAPHICS_DIR = os.path.join(_SRC_LIB, "graphics")

#: Absolute path to the ``displaysys`` package directory, handy for tests that
#: want to copy it somewhere isolated.
DISPLAYSYS_DIR = os.path.join(_SRC_LIB, "displaysys")
