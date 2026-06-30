"""
ensure_nano_gui.py - Install Peter Hinch's nano-gui into add_ons/ when missing.

Used by examples that import gui.*. No-op when gui is already present or mip
is unavailable (e.g. CPython without mip).
"""


def _add_ons_dir():
    return __file__.replace("\\", "/").rsplit("/", 1)[0]


def _has_nano_gui():
    try:
        import gui.core.nanogui  # noqa: F401

        return True
    except ImportError:
        return False


def ensure_nano_gui():
    """Install nano-gui into add_ons/ if gui is not importable. Returns True when ready."""
    if _has_nano_gui():
        return True
    try:
        import mip
    except ImportError:
        return False
    mip.install("github:peterhinch/micropython-nano-gui", target=_add_ons_dir())
    return _has_nano_gui()
