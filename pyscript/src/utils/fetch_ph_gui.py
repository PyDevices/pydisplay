"""
fetch_ph_gui.py - Install one Peter Hinch GUI into utils/gui/.

Supported ``which`` values (full upstream repo names):
  micropython-nano-gui, micropython-micro-gui, micropython-touch

Only one ``gui/`` tree is active at a time. If a different core is present, the
directory is emptied before installing. Host compatibility changes are
in-memory only (no edits under ``gui/``).

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
    "micropython-nano-gui": "github:PyDevices/pydevices-examples/packages/micropython-nano-gui.json",
    "micropython-micro-gui": "github:PyDevices/pydevices-examples/packages/micropython-micro-gui.json",
    "micropython-touch": "github:PyDevices/pydevices-examples/packages/micropython-touch.json",
}

# colors.py imports SSD from color_setup, which re-enters fetch_ph_gui while
# gui.core.* is mid-import during patching. Treat nested calls as success.
_IN_FETCH = False


def _utils_dir():
    # CPython (esp. Windows PE under WSL UNC) needs native separators so mip
    # can mkdir/open install targets. MP/CP have no ``os.path``.
    import sys

    if sys.implementation.name == "cpython":
        import os

        return os.path.dirname(__file__)
    return __file__.replace("\\", "/").rsplit("/", 1)[0]


def _gui_dir():
    import sys

    if sys.implementation.name == "cpython":
        import os

        return os.path.join(_utils_dir(), "gui")
    return _utils_dir() + "/gui"


def _detect_core():
    """Return which repo name is installed, or None. Uses files only (no import)."""
    import os
    import sys

    found = []
    if sys.implementation.name == "cpython":
        core = os.path.join(_gui_dir(), "core")
        for which, fname in _CORE_FILES.items():
            try:
                os.stat(os.path.join(core, fname))
                found.append(which)
            except OSError:
                pass
    else:
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
    """Stub machine.Pin on hosts that lack it.

    Covers CPython desktop, MicroPython-WASM, and unix MicroPython (``machine``
    exists but has no ``Pin`` — only ``PinBase`` / ``Signal``). Unix MP's
    native ``machine`` rejects ``setattr`` (``AttributeError``), so when Pin is
    missing we replace ``sys.modules['machine']`` with a thin proxy that exposes
    the stub and forwards other attributes.

    Uses a plain class instance rather than ``types.ModuleType(name)`` — the
    latter's attribute exists on MicroPython-WASM but its constructor raises
    ``TypeError: can't create 'module' instances`` (native runtime
    limitation). A plain object works identically for ``sys.modules``
    caching: ``import machine`` returns whatever is registered there.
    """
    import sys

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

    mod = sys.modules.get("machine")
    if mod is None:
        try:
            import machine as mod  # noqa: F811
        except ImportError:
            mod = None

    if mod is not None and hasattr(mod, "Pin"):
        return

    if mod is not None:
        try:
            mod.Pin = Pin
            if hasattr(mod, "Pin"):
                return
        except (AttributeError, TypeError):
            pass

        class _MachineProxy:
            def __init__(self, real, pin):
                self._real = real
                self.Pin = pin

            def __getattr__(self, name):
                return getattr(self._real, name)

        sys.modules["machine"] = _MachineProxy(mod, Pin)
        return

    class _FakeMachineModule:
        pass

    fake = _FakeMachineModule()
    fake.Pin = Pin
    sys.modules["machine"] = fake


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
        _prime_primitives()


def fetch_ph_gui(which, apply_patches=True):
    """Ensure ``which`` GUI is in utils/gui/ and optionally patched.

    Returns True when ready. Pass ``apply_patches=False`` when pre-seeding
    (e.g. PyScript loader) before the setup module defines ``SSD`` — callers
    that import ``color_setup`` / ``hardware_setup`` / ``touch_setup`` will
    call again with patches enabled.

    Uses ``mip.install`` (firmware on MicroPython; portable ``mip.py`` from
    pydevices ``utils/`` on CPython / Pyodide / CircuitPython).
    """
    global _IN_FETCH

    if which not in _CORE_FILES:
        raise ValueError(
            "which must be micropython-nano-gui, micropython-micro-gui, or micropython-touch"
        )

    if _IN_FETCH:
        return _detect_core() == which

    _IN_FETCH = True
    try:
        present = _detect_core()
        if present == which:
            if apply_patches:
                _apply_patches(which)
            return True

        if present is not None or _gui_exists():
            _empty_gui()

        try:
            import mip
        except ImportError:
            return False

        try:
            mip.install(_PACKAGES[which], target=_utils_dir(), mpy=False)
        except Exception:
            return False

        _purge_gui_modules()
        if _detect_core() == which:
            if apply_patches:
                _apply_patches(which)
            return True
        return False
    finally:
        _IN_FETCH = False
