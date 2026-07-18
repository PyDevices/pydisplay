# SPDX-License-Identifier: MIT
"""SDL keycode → LVGL KEY_* mapping + multi-group focus navigation."""

import lvgl as lv

try:
    from eventsys.keys import Keys
except ImportError:
    Keys = None

try:
    import eventsys
    from eventsys import events
except ImportError:
    eventsys = None
    events = None

# Captured when display_driver expands HOST → VirtualDevices (see capture_virtual_devices).
_keypad_vdev = None
_vehicle = None
_focus_nav = None
_capture_done = False


def _key_const(name, default):
    if Keys is None:
        return default
    return getattr(Keys, name, default)


_SDL_UP = _key_const("K_UP", 1073741906)
_SDL_DOWN = _key_const("K_DOWN", 1073741905)
_SDL_LEFT = _key_const("K_LEFT", 1073741904)
_SDL_RIGHT = _key_const("K_RIGHT", 1073741903)
_SDL_RETURN = _key_const("K_RETURN", 13)
_SDL_KP_ENTER = _key_const("K_KP_ENTER", 1073741912)

_DIGIT_KEYS = {}
for _i in range(10):
    _DIGIT_KEYS[_key_const("K_%d" % _i, 48 + _i)] = _i
if Keys is not None:
    _DIGIT_KEYS[Keys.K_KP_0] = 0
    for _i in range(1, 10):
        _DIGIT_KEYS[getattr(Keys, "K_KP_%d" % _i)] = _i


def remap_nav_key(sdl_key):
    """Map eventsys/SDL key codes to lv.KEY for group navigation."""
    if sdl_key == _SDL_UP:
        return lv.KEY.UP
    if sdl_key == _SDL_DOWN:
        return lv.KEY.DOWN
    if sdl_key == _SDL_LEFT:
        return lv.KEY.LEFT
    if sdl_key == _SDL_RIGHT:
        return lv.KEY.RIGHT
    if sdl_key in (_SDL_RETURN, _SDL_KP_ENTER):
        return lv.KEY.ENTER
    return None


def digit_from_key(sdl_key):
    return _DIGIT_KEYS.get(sdl_key)


def capture_virtual_devices():
    """Call before ``import display_driver`` so we can re-subscribe the keypad vdev."""
    global _keypad_vdev, _capture_done
    if eventsys is None or _capture_done:
        return
    VD = eventsys.VirtualDevices
    _orig_init = VD.__init__

    def _wrapped_init(self, host_device):
        _orig_init(self, host_device)
        global _keypad_vdev
        _keypad_vdev = self._vd_keypad

    VD.__init__ = _wrapped_init
    _capture_done = True


def _find_keypad_indev():
    """Return the LVGL keypad indev created by display_driver, if any."""
    if _keypad_vdev is not None:
        ud = getattr(_keypad_vdev, "user_data", None)
        if ud is not None:
            return ud
    # Fallback: scan indevs
    try:
        indev = lv.indev_get_next(None)
        while indev is not None:
            try:
                if indev.get_type() == lv.INDEV_TYPE.KEYPAD:
                    return indev
            except Exception:
                pass
            try:
                indev = lv.indev_get_next(indev)
            except Exception:
                break
    except Exception:
        pass
    return None


def _mapped_keypad_cb(event, indev, data):
    """Replacement for display_driver._keypad_cb.

    Arrows → FocusNav (KEYPAD indev only auto-navigates on KEY_NEXT/PREV).
    Enter  → remapped lv.KEY.ENTER for the active group.
    Digits are ignored (vehicle drive profile is automatic).
    """
    if event is None or events is None:
        return

    nav = _focus_nav

    if event.type == events.KEYDOWN:
        if digit_from_key(event.key) is not None:
            data.state = lv.INDEV_STATE.RELEASED
            data.key = 0
            return

        mapped = remap_nav_key(event.key)
        if mapped is not None and mapped != lv.KEY.ENTER and nav is not None:
            # Consume arrows ourselves — KEYPAD won't focus_next on UP/DOWN.
            nav.handle_nav_key(mapped)
            data.state = lv.INDEV_STATE.RELEASED
            data.key = 0
            return

        data.state = lv.INDEV_STATE.PRESSED
        data.key = mapped if mapped is not None else event.key

    elif event.type == events.KEYUP:
        if digit_from_key(event.key) is not None:
            data.state = lv.INDEV_STATE.RELEASED
            data.key = 0
            return

        mapped = remap_nav_key(event.key)
        if mapped is not None and mapped != lv.KEY.ENTER and nav is not None:
            data.state = lv.INDEV_STATE.RELEASED
            data.key = 0
            return

        data.state = lv.INDEV_STATE.RELEASED
        data.key = mapped if mapped is not None else event.key


class InputBridge:
    """Install SDL→LVGL key mapping and bind FocusNav to the keypad indev."""

    def __init__(self, runtime, vehicle, focus_nav=None):
        self.runtime = runtime
        self.vehicle = vehicle
        self.focus_nav = focus_nav

    def install(self):
        global _vehicle, _focus_nav
        _vehicle = self.vehicle
        _focus_nav = self.focus_nav

        import display_driver

        display_driver._keypad_cb = _mapped_keypad_cb
        if _keypad_vdev is not None:
            _keypad_vdev.subscribe(_mapped_keypad_cb)

        if self.focus_nav is not None:
            indev = _find_keypad_indev()
            if indev is not None:
                self.focus_nav.bind_keypad_indev(indev)
