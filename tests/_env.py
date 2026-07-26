# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts pydisplay packages on ``sys.path``.

Puts ``src/lib`` (displaysys, eventsys, multimer) and ``src/add_ons`` on
``sys.path`` without installing anything. Does **not** require sibling git
checkouts or optional packages such as ``graphics`` / ``usdl2``.

    import _env  # noqa: F401
    import multimer
    import eventsys
    import displaysys
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_LIB = os.path.join(_REPO_ROOT, "src", "lib")
_SRC_ADDONS = os.path.join(_REPO_ROOT, "src", "add_ons")

if _SRC_LIB not in sys.path:
    sys.path.insert(0, _SRC_LIB)
if _SRC_ADDONS not in sys.path:
    sys.path.insert(0, _SRC_ADDONS)

#: Absolute path to the ``multimer`` package directory.
MULTIMER_DIR = os.path.join(_SRC_LIB, "multimer")

#: Absolute path to the ``eventsys`` package directory.
EVENTSYS_DIR = os.path.join(_SRC_LIB, "eventsys")

#: Absolute path to the ``displaysys`` package directory.
DISPLAYSYS_DIR = os.path.join(_SRC_LIB, "displaysys")


def _ensure_micropython_shim():
    """CPython unit tests may import MCU-oriented helpers that expect ``micropython``."""
    if "micropython" in sys.modules:
        return
    import types

    mp = types.ModuleType("micropython")
    mp.const = lambda x: x

    def _alloc_emergency_exception_buf(_size):
        pass

    mp.alloc_emergency_exception_buf = _alloc_emergency_exception_buf
    sys.modules["micropython"] = mp


_ensure_micropython_shim()
