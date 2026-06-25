# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts ``multimer`` on ``sys.path``.

The tests are self-contained: importing this module makes ``src/lib`` (where
the ``multimer`` package lives) importable without installing anything. Import
it before importing ``multimer`` in any test module::

    import _env  # noqa: F401
    import multimer
"""

import os
import sys

_SRC_LIB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "lib"))

if _SRC_LIB not in sys.path:
    sys.path.insert(0, _SRC_LIB)

#: Absolute path to the ``multimer`` package directory, handy for tests that
#: want to copy it somewhere isolated.
MULTIMER_DIR = os.path.join(_SRC_LIB, "multimer")
