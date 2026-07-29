"""Put '', .frozen (MP/CP), lib first on sys.path; append _extra_dirs."""

import os
import sys

__all__ = ["add", "cwd", "update"]
_extra_dirs = ("add_ons", "examples")


def cwd():
    path = os.getcwd()
    return path if path[-1] == "/" else path + "/"


def _exists(name):
    if name in ("", ".frozen"):
        return True
    path = name if name.startswith("/") else cwd() + name
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def add(directory, front=False):
    if not _exists(directory):
        return
    if directory in sys.path:
        sys.path.remove(directory)
    if front:
        sys.path.insert(0, directory)
    else:
        sys.path.append(directory)


def update():
    # Prepend in reverse so the final order is '', .frozen, lib.
    add("lib", front=True)
    if sys.implementation.name in ("micropython", "circuitpython"):
        add(".frozen", front=True)
    add("", front=True)
    for directory in _extra_dirs:
        add(directory)
    try:
        import pydisplay_test_mode

        quiet = pydisplay_test_mode.ENABLED
    except ImportError:
        quiet = False
    if not quiet:
        print("path.py:  updated sys.path.")


update()
