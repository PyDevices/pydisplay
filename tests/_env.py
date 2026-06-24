# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts ``graphics`` on ``sys.path``.

The tests are self-contained: importing this module makes ``src/lib`` (where
the ``graphics`` package lives) importable without installing anything. Import
it before importing ``graphics`` in any test module::

    import _env  # noqa: F401
    import graphics
"""

import os
import sys

SRC_LIB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "lib"))

if SRC_LIB not in sys.path:
    sys.path.insert(0, SRC_LIB)

#: Absolute path to the ``graphics`` package directory, handy for tests that
#: want to copy it somewhere isolated.
GRAPHICS_DIR = os.path.join(SRC_LIB, "graphics")
