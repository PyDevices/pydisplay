# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Platform capability registry for multimer."""

import sys

_DIALECT = sys.implementation.name

_CAPS = {
    "backend": None,
    "needs_pump": False,
    "schedule_queue": False,
    "async_available": False,
    "dialect": _DIALECT,
}


class UnsupportedPlatformError(ImportError):
    """Raised when no sync Timer backend is available on this platform."""


def init_capabilities(*, backend, needs_pump, schedule_queue=None):
    """Record the selected sync Timer backend and related flags."""
    if schedule_queue is None:
        from ._schedule import SCHEDULE_QUEUE

        schedule_queue = SCHEDULE_QUEUE
    _CAPS["backend"] = backend
    _CAPS["needs_pump"] = needs_pump
    _CAPS["schedule_queue"] = schedule_queue
    _CAPS["dialect"] = _DIALECT
    _update_async_available()


def _update_async_available():
    try:
        from . import _async  # noqa: F401
    except ImportError:
        _CAPS["async_available"] = False
    else:
        _CAPS["async_available"] = True


def capabilities():
    """Return a snapshot of platform timer capabilities."""
    return dict(_CAPS)


def needs_pump():
    """Return True when the main loop must call ``pump()`` for sync timers."""
    return _CAPS["needs_pump"]


def backend_name():
    """Return the name of the active sync Timer backend."""
    return _CAPS["backend"]
