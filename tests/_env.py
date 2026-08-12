# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Put pydevices-examples utilities and canonical sibling products on ``sys.path``."""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_UTILS = os.path.join(_REPO_ROOT, "src", "utils")

if _SRC_UTILS not in sys.path:
    sys.path.insert(0, _SRC_UTILS)

_HARDWARE_ROOT_CANDIDATES = (
    os.path.join(_REPO_ROOT, "..", "pydevices"),
    os.path.join(_REPO_ROOT, "pydevices"),
)
_HARDWARE_ROOT = None
for _hw in _HARDWARE_ROOT_CANDIDATES:
    _hw = os.path.abspath(_hw)
    if os.path.isdir(_hw):
        _HARDWARE_ROOT = _hw
        _hw_lib = os.path.join(_hw, "lib")
        _hw_utils = os.path.join(_hw, "utils")
        if os.path.isdir(_hw_lib) and _hw_lib not in sys.path:
            sys.path.insert(0, _hw_lib)
        if os.path.isdir(_hw_utils) and _hw_utils not in sys.path:
            sys.path.insert(0, _hw_utils)
        break

if _HARDWARE_ROOT:
    _hw_display = os.path.join(_HARDWARE_ROOT, "drivers", "display")
    if os.path.isdir(_hw_display) and _hw_display not in sys.path:
        sys.path.insert(0, _hw_display)
