"""Put '', .frozen (MP/CP), lib, utils first on sys.path."""

import os
import sys

__all__ = ["add", "cwd", "update"]
_extra_dirs = ("utils",)


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
    # Prepend in reverse so the final order is:
    # '', .frozen, lib, utils, <stdlib...>
    # utils must precede the stdlib so ``import secrets`` resolves to
    # utils/secrets.py on CPython (stdlib also ships a ``secrets`` module).
    for directory in reversed(_extra_dirs):
        add(directory, front=True)
    add("lib", front=True)
    # Desktop sibling checkout: events.py / keys.py / multimer in hardware lib/.
    for candidate in ("../pydevices/lib", "../../pydevices/lib"):
        if _exists(candidate):
            add(candidate, front=True)
            break
    # byteswap, mip, viper_tools, keypins, wifi, frame_recorder, micropython shim.
    for candidate in ("../pydevices/utils", "../../pydevices/utils"):
        if _exists(candidate):
            add(candidate, front=True)
            break
    # displaydev package lives in hardware drivers/display/.
    for candidate in (
        "../pydevices/drivers/display",
        "../../pydevices/drivers/display",
    ):
        if _exists(candidate):
            add(candidate, front=True)
            break
    if sys.implementation.name in ("micropython", "circuitpython"):
        add(".frozen", front=True)
    add("", front=True)
    try:
        import pydevices_test_mode

        quiet = pydevices_test_mode.ENABLED
    except ImportError:
        quiet = False
    if not quiet:
        print("path.py:  updated sys.path.")


update()
