"""
fetch_ph_gui.py - Install one Peter Hinch GUI into add_ons/gui/ and patch FrameBuffer checks.

Supported ``which`` values (full upstream repo names):
  micropython-nano-gui, micropython-micro-gui, micropython-touch

Only one ``gui/`` tree is active at a time. If a different core is present, the
directory is emptied before installing. Patches are in-memory only (no edits
under ``gui/``).

Callers must define ``SSD`` on their setup module before calling fetch, because
``gui.core.colors`` imports ``SSD`` from ``color_setup`` / ``hardware_setup`` /
``touch_setup``.
"""

_CORE_FILES = {
    "micropython-nano-gui": "nanogui.py",
    "micropython-micro-gui": "ugui.py",
    "micropython-touch": "tgui.py",
}

_PACKAGES = {
    "micropython-nano-gui": "github:PyDevices/pydisplay/packages/micropython-nano-gui.json",
    "micropython-micro-gui": "github:PyDevices/pydisplay/packages/micropython-micro-gui.json",
    "micropython-touch": "github:PyDevices/pydisplay/packages/micropython-touch.json",
}


def _add_ons_dir():
    return __file__.replace("\\", "/").rsplit("/", 1)[0]


def _gui_dir():
    return _add_ons_dir() + "/gui"


def _core_path(which):
    return _gui_dir() + "/core/" + _CORE_FILES[which]


def _detect_core():
    """Return which repo name is installed, or None. Uses files only (no import)."""
    import os

    found = []
    for which, fname in _CORE_FILES.items():
        try:
            os.stat(_gui_dir() + "/core/" + fname)
            found.append(which)
        except OSError:
            pass
    if len(found) == 1:
        return found[0]
    return None


def _purge_gui_modules():
    import sys

    for name in list(sys.modules):
        if name == "gui" or name.startswith("gui."):
            del sys.modules[name]


def _rmtree(path):
    import os

    try:
        names = os.listdir(path)
    except OSError:
        return
    for name in names:
        child = path + "/" + name
        try:
            os.remove(child)
        except OSError:
            _rmtree(child)
            try:
                os.rmdir(child)
            except OSError:
                pass
    try:
        os.rmdir(path)
    except OSError:
        pass


def _empty_gui():
    _purge_gui_modules()
    _rmtree(_gui_dir())


def _gui_exists():
    import os

    try:
        os.listdir(_gui_dir())
        return True
    except OSError:
        return False


def _patch_writer():
    """Accept graphics.FrameBuffer where writer._get_id checks builtin framebuf."""
    try:
        import framebuf
        import gui.core.writer as wr

        from graphics import FrameBuffer as GfxFrameBuffer
    except ImportError:
        return
    if getattr(wr, "_pydisplay_fb_patch", False):
        return

    def _get_id(device):
        if not (isinstance(device, framebuf.FrameBuffer) or isinstance(device, GfxFrameBuffer)):
            raise ValueError("Device must be derived from FrameBuffer.")
        return id(device)

    wr._get_id = _get_id
    wr._pydisplay_fb_patch = True


def _patch_nanogui_refresh():
    """Accept graphics.FrameBuffer where nanogui.refresh checks builtin framebuf."""
    try:
        import framebuf
        import gui.core.nanogui as ng

        from graphics import FrameBuffer as GfxFrameBuffer
    except ImportError:
        return
    if getattr(ng.refresh, "_pydisplay_fb_patch", False):
        return

    def refresh(device, clear=False):
        if not (isinstance(device, framebuf.FrameBuffer) or isinstance(device, GfxFrameBuffer)):
            raise ValueError("Device must be derived from FrameBuffer.")
        if device not in ng.DObject.devices:
            ng.DObject.devices[device] = set()
            device.fill(0)
        else:
            if clear:
                ng.DObject.devices[device].clear()
                device.fill(0)
            else:
                for obj in ng.DObject.devices[device]:
                    obj.show()
                ng.DObject.devices[device].clear()
        device.show()

    refresh._pydisplay_fb_patch = True
    ng.refresh = refresh


def _patch_time_ticks():
    """CPython lacks MicroPython time.ticks_*; ugui/tgui import them at load."""
    import time

    if not hasattr(time, "ticks_ms"):

        def ticks_ms():
            return int(time.time() * 1000)

        def ticks_diff(a, b):
            return a - b

        def ticks_add(a, b):
            return a + b

        time.ticks_ms = ticks_ms
        time.ticks_diff = ticks_diff
        time.ticks_add = ticks_add
        if not hasattr(time, "sleep_ms"):

            def sleep_ms(ms):
                time.sleep(ms / 1000.0)

            time.sleep_ms = sleep_ms


def _patch_machine_pin():
    """Stub machine.Pin on hosts that lack it (CPython desktop)."""
    import sys

    if "machine" in sys.modules:
        return
    try:
        import machine  # noqa: F401

        return
    except ImportError:
        pass

    class Pin:
        IN = 0
        OUT = 1
        OPEN_DRAIN = 2
        PULL_UP = 1
        PULL_DOWN = 2

        def __init__(self, *args, **kwargs):
            self._v = 1

        def value(self, v=None):
            if v is None:
                return self._v
            self._v = v
            return None

        def irq(self, *args, **kwargs):
            return None

    try:
        import types

        mod = types.ModuleType("machine")
    except (ImportError, AttributeError):
        # MicroPython without types.ModuleType — should have real machine
        return
    mod.Pin = Pin
    sys.modules["machine"] = mod


def _prime_primitives():
    """Make gui.primitives lazy imports work on CPython (MP-style __import__)."""
    try:
        import importlib

        from gui import primitives
    except ImportError:
        return

    attrs = getattr(primitives, "_attrs", None)
    if not attrs:
        return

    def _getattr(attr):
        mod = attrs.get(attr, None)
        if mod is None:
            raise AttributeError(attr)
        value = getattr(importlib.import_module("." + mod, "gui.primitives"), attr)
        setattr(primitives, attr, value)
        return value

    primitives.__getattr__ = _getattr


def _patch_uasyncio():
    """Alias uasyncio -> asyncio on CPython."""
    import sys

    if "uasyncio" in sys.modules:
        return
    try:
        import uasyncio  # noqa: F401

        return
    except ImportError:
        import asyncio

        sys.modules["uasyncio"] = asyncio


def _patch_utime():
    """Alias utime -> time on CPython (after ticks_* are installed)."""
    import sys
    import time

    if "utime" in sys.modules:
        return
    try:
        import utime  # noqa: F401

        return
    except ImportError:
        sys.modules["utime"] = time


def _patch_micropython_const():
    """Provide ``const`` builtin used by ugui/tgui on MicroPython."""
    import builtins

    if hasattr(builtins, "const"):
        return
    try:
        from micropython import const as _const
    except ImportError:

        def _const(x):
            return x

    builtins.const = _const


def _apply_patches(which):
    if which in ("micropython-micro-gui", "micropython-touch"):
        _patch_micropython_const()
        _patch_time_ticks()
        _patch_utime()
        _patch_machine_pin()
        _patch_uasyncio()
    _patch_writer()
    if which == "micropython-nano-gui":
        _patch_nanogui_refresh()
    if which in ("micropython-micro-gui", "micropython-touch"):
        _prime_primitives()


def fetch_ph_gui(which):
    """Ensure ``which`` GUI is in add_ons/gui/ and patched. Returns True when ready."""
    if which not in _CORE_FILES:
        raise ValueError(
            "which must be micropython-nano-gui, micropython-micro-gui, or micropython-touch"
        )

    present = _detect_core()
    if present == which:
        _apply_patches(which)
        return True

    try:
        import mip
    except ImportError:
        # Cannot install or switch without mip; do not wipe an existing tree.
        return False

    if present is not None or _gui_exists():
        _empty_gui()

    mip.install(_PACKAGES[which], target=_add_ons_dir())
    _purge_gui_modules()
    if _detect_core() == which:
        _apply_patches(which)
        return True
    return False
