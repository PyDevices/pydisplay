# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts ``displaysys`` on ``sys.path``.

The tests are self-contained: importing this module makes ``src/lib`` (where
the ``displaysys`` package lives) importable without installing anything.
Import it before importing ``displaysys`` in any test module::

    import _env  # noqa: F401
    import displaysys
"""

import os
import sys

_SRC_LIB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "lib"))

if _SRC_LIB not in sys.path:
    sys.path.insert(0, _SRC_LIB)

#: Absolute path to the ``displaysys`` package directory, handy for tests that
#: want to copy it somewhere isolated.
DISPLAYSYS_DIR = os.path.join(_SRC_LIB, "displaysys")
