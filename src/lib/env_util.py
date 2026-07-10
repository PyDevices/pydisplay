# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cross-runtime environment variable helpers (CPython, MicroPython, CircuitPython)."""

# Process-local overrides for ports without ``os.environ`` / ``os.putenv``.
_overrides = {}


def env_set(name, value):
    """Set an environment variable portably (CPython, MicroPython, CircuitPython).

    Always records a process-local override so ``env_bool`` / ``env_get`` see the
    value even when the host ``os`` module has no ``environ``. When available,
    also updates ``os.environ`` or calls ``os.putenv``.
    """
    text = "" if value is None else str(value)
    _overrides[name] = text

    import os

    environ = getattr(os, "environ", None)
    if environ is not None:
        try:
            environ[name] = text
            return
        except Exception:
            pass
    putenv = getattr(os, "putenv", None)
    if putenv is not None:
        try:
            putenv(name, text)
        except Exception:
            pass


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
    if name in _overrides:
        return _overrides[name]

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
