# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts pydisplay packages on ``sys.path``.

Puts ``src/lib`` (``eventsys``) and ``src/utils`` on ``sys.path`` without
installing anything. When a sibling (or nested) ``micropython-hardware`` tree
is present, ``lib/`` (``events``, ``keys``, ``multimer``) is added so
``eventsys`` can import its hardware dependencies.

    import _env  # noqa: F401
    import eventsys
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_LIB = os.path.join(_REPO_ROOT, "src", "lib")
_SRC_UTILS = os.path.join(_REPO_ROOT, "src", "utils")

if _SRC_LIB not in sys.path:
    sys.path.insert(0, _SRC_LIB)
if _SRC_UTILS not in sys.path:
    sys.path.insert(0, _SRC_UTILS)

_HARDWARE_ROOT_CANDIDATES = (
    os.path.join(_REPO_ROOT, "..", "micropython-hardware"),
    os.path.join(_REPO_ROOT, "micropython-hardware"),
)
_HARDWARE_ROOT = None
for _hw in _HARDWARE_ROOT_CANDIDATES:
    _hw = os.path.abspath(_hw)
    if os.path.isdir(_hw):
        _HARDWARE_ROOT = _hw
        _hw_lib = os.path.join(_hw, "lib")
        if os.path.isdir(_hw_lib) and _hw_lib not in sys.path:
            sys.path.insert(0, _hw_lib)
        break

#: Absolute path to the ``eventsys`` package directory.
EVENTSYS_DIR = os.path.join(_SRC_LIB, "eventsys")

#: Shared ``events.py`` / ``keys.py`` (micropython-hardware/lib).
EVENTS_PY = os.path.join(_HARDWARE_ROOT, "lib", "events.py") if _HARDWARE_ROOT else ""
KEYS_PY = os.path.join(_HARDWARE_ROOT, "lib", "keys.py") if _HARDWARE_ROOT else ""
