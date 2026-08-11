# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts pydisplay packages on ``sys.path``.

Puts ``src/lib`` (eventsys; ``displaydev`` / ``multimer`` symlinks) and
``src/utils`` on ``sys.path`` without installing anything. When a sibling (or
nested) ``micropython-hardware`` tree is present, ``lib/`` (``events``,
``keys``, ``multimer``), ``drivers/`` (``boarddev``), and ``drivers/display``
(``displaydev``) are added. Does **not** require optional packages such as
``pygraphics`` / ``usdl2``.

    import _env  # noqa: F401
    import multimer
    import eventsys
    import displaydev
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

# Optional: events/keys/multimer (lib/), boarddev (drivers/), displaydev
# (drivers/display) from micropython-hardware.
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
        _hw_drivers = os.path.join(_hw, "drivers")
        _hw_display = os.path.join(_hw, "drivers", "display")
        if os.path.isdir(_hw_lib) and _hw_lib not in sys.path:
            sys.path.insert(0, _hw_lib)
        if os.path.isdir(_hw_drivers) and _hw_drivers not in sys.path:
            sys.path.insert(0, _hw_drivers)
        if os.path.isdir(_hw_display) and _hw_display not in sys.path:
            sys.path.insert(0, _hw_display)
        break

#: Absolute path to the ``eventsys`` package directory.
EVENTSYS_DIR = os.path.join(_SRC_LIB, "eventsys")

#: Absolute path to the ``multimer`` package directory (hardware).
MULTIMER_DIR = (
    os.path.join(_HARDWARE_ROOT, "lib", "multimer")
    if _HARDWARE_ROOT
    else os.path.join(_SRC_LIB, "multimer")
)

#: Absolute path to the ``displaydev`` package directory (hardware).
DISPLAYDEV_DIR = (
    os.path.join(_HARDWARE_ROOT, "drivers", "display", "displaydev")
    if _HARDWARE_ROOT
    else os.path.join(_SRC_LIB, "displaydev")
)

#: Shared ``events.py`` / ``keys.py`` (micropython-hardware/lib).
EVENTS_PY = os.path.join(_HARDWARE_ROOT, "lib", "events.py") if _HARDWARE_ROOT else ""
KEYS_PY = os.path.join(_HARDWARE_ROOT, "lib", "keys.py") if _HARDWARE_ROOT else ""


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
