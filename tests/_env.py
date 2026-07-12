# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared test bootstrap that puts pydisplay packages on ``sys.path``.

The tests are self-contained: importing this module makes ``src/lib`` (where
``eventsys``, ``graphics``, ``displaysys``, and ``multimer`` live) importable
without installing anything. Import it
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
_SRC_ADDONS = os.path.join(_REPO_ROOT, "src", "add_ons")

if _SRC_LIB not in sys.path:
    sys.path.insert(0, _SRC_LIB)
if _SRC_ADDONS not in sys.path:
    sys.path.insert(0, _SRC_ADDONS)


def _sync_graphics_framebuf():
    """Materialize ``graphics/framebuf.py`` from ``add_ons/framebuf.py`` (single source)."""
    import subprocess

    sync = os.path.join(_REPO_ROOT, "scripts", "install_sync_framebuf.py")
    subprocess.run([sys.executable, sync], cwd=_REPO_ROOT, check=True)


_sync_graphics_framebuf()

#: Absolute path to the ``multimer`` package directory.
MULTIMER_DIR = os.path.join(_SRC_LIB, "multimer")

#: Absolute path to the ``eventsys`` package directory, handy for tests that
#: want to copy it somewhere isolated.
EVENTSYS_DIR = os.path.join(_SRC_LIB, "eventsys")

#: Absolute path to the ``graphics`` package directory, handy for tests that
#: want to copy it somewhere isolated.
GRAPHICS_DIR = os.path.join(_SRC_LIB, "graphics")

#: Absolute path to the ``displaysys`` package directory, handy for tests that
#: want to copy it somewhere isolated.
DISPLAYSYS_DIR = os.path.join(_SRC_LIB, "displaysys")

_DRIVERS_DISPLAY = os.path.join(_REPO_ROOT, "drivers", "display")
_DRIVERS_BUS = os.path.join(_REPO_ROOT, "drivers", "bus")
_DRIVERS_TOUCH = os.path.join(_REPO_ROOT, "drivers", "touch")
_DRIVERS_INPUT = os.path.join(_REPO_ROOT, "drivers", "input")

for _path in (_DRIVERS_DISPLAY, _DRIVERS_BUS, _DRIVERS_TOUCH, _DRIVERS_INPUT):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def _ensure_micropython_shim():
    """CPython unit tests import MCU-oriented drivers that expect ``micropython``."""
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
