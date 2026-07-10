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


def _patch_nano_gui_framebuffer_check():
    """Accept graphics.FrameBuffer (cmod) where nano-gui checks builtin framebuf."""
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


def ensure_nano_gui():
    """Install nano-gui into add_ons/ if gui is not importable. Returns True when ready."""
    if _has_nano_gui():
        _patch_nano_gui_framebuffer_check()
        return True
    try:
        import mip
    except ImportError:
        return False
    mip.install("github:peterhinch/micropython-nano-gui", target=_add_ons_dir())
    if _has_nano_gui():
        _patch_nano_gui_framebuffer_check()
        return True
    return False
