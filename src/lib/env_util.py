# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cross-runtime environment variable helpers (CPython, MicroPython, CircuitPython)."""


def env_bool(name, default=False):
    """Read a truthy/falsey environment variable with a portable fallback chain."""
    raw = _env_raw(name)
    if raw is None:
        return bool(default)
    text = str(raw).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off"):
        return False
    return bool(default)


def _env_raw(name):
    import os

    environ = getattr(os, "environ", None)
    if environ is not None:
        try:
            value = environ.get(name)
        except Exception:
            value = None
        if value is not None:
            return value
    getenv = getattr(os, "getenv", None)
    if getenv is None:
        return None
    try:
        return getenv(name)
    except Exception:
        return None
