# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.psdisplay
"""

from js import console, document
from pyscript.ffi import create_proxy

from displaysys import DisplayDriver, color_rgb
from eventsys import events
from eventsys.keys import Keys


def log(*args):
    console.log(*args)


# ---------------------------------------------------------------------------
# Keyboard mapping
#
# Translate browser ``KeyboardEvent`` values into eventsys (SDL-style) key
# codes so the events produced here match the QUEUE backends (SDL2 / PyGame).
# ``KeyboardEvent.key`` holds either a single printable character (mapped by
# code point below) or a named value such as ``"ArrowUp"`` (mapped via the
# table).  The table is kept local to this module by design.
# ---------------------------------------------------------------------------
_NAMED_KEYS = {
    "Backspace": Keys.K_BACKSPACE,
    "Tab": Keys.K_TAB,
    "Enter": Keys.K_RETURN,
    "Escape": Keys.K_ESCAPE,
    "Delete": Keys.K_DELETE,
    "ArrowUp": Keys.K_UP,
    "ArrowDown": Keys.K_DOWN,
    "ArrowLeft": Keys.K_LEFT,
    "ArrowRight": Keys.K_RIGHT,
    "Home": Keys.K_HOME,
    "End": Keys.K_END,
    "PageUp": Keys.K_PAGEUP,
    "PageDown": Keys.K_PAGEDOWN,
    "Insert": Keys.K_INSERT,
    "CapsLock": Keys.K_CAPSLOCK,
    "NumLock": Keys.K_NUMLOCKCLEAR,
    "ScrollLock": Keys.K_SCROLLLOCK,
    "Pause": Keys.K_PAUSE,
    "PrintScreen": Keys.K_PRINTSCREEN,
    "ContextMenu": Keys.K_MENU,
    "Control": Keys.K_LCTRL,
    "Shift": Keys.K_LSHIFT,
    "Alt": Keys.K_LALT,
    "Meta": Keys.K_LGUI,
    "F1": Keys.K_F1,
    "F2": Keys.K_F2,
    "F3": Keys.K_F3,
    "F4": Keys.K_F4,
    "F5": Keys.K_F5,
    "F6": Keys.K_F6,
    "F7": Keys.K_F7,
    "F8": Keys.K_F8,
    "F9": Keys.K_F9,
    "F10": Keys.K_F10,
    "F11": Keys.K_F11,
    "F12": Keys.K_F12,
}

_MOD_GROUPS = (Keys.KMOD_CTRL, Keys.KMOD_SHIFT, Keys.KMOD_ALT, Keys.KMOD_GUI)


def _key_to_keycode(key):
    """Map a DOM ``KeyboardEvent.key`` value to an eventsys key code."""
    code = _NAMED_KEYS.get(key)
    if code is not None:
        return code
    if key and len(key) == 1:
        o = ord(key)
        if 0x41 <= o <= 0x5A:  # 'A'-'Z' -> lowercase code, matching SDL
            return o + 0x20
        return o
    return Keys.K_UNKNOWN


def _mod_mask(ctrl, shift, alt, meta):
    """Build an eventsys modifier mask from DOM modifier flags."""
    mask = 0
    if shift:
        mask |= Keys.KMOD_LSHIFT
    if ctrl:
        mask |= Keys.KMOD_LCTRL
    if alt:
        mask |= Keys.KMOD_LALT
    if meta:
        mask |= Keys.KMOD_LGUI
    return mask


def _chord_matches(chord, keycode, mod):
    """Return True if (keycode, mod) satisfies a ``(key, mod_mask)`` chord."""
    if not chord:
        return False
    chord_key, chord_mod = chord
    if keycode != chord_key:
        return False
    for group in _MOD_GROUPS:
        if (chord_mod & group) and not (mod & group):
            return False
    return True


class PSTouch:
    """
    Mouse/touch input for a PyScript canvas.

    Wraps a single HTML ``<canvas>`` element and tracks the pointer position
    while the left mouse button is held, exposing it through
    :meth:`get_mouse_pos`.  Intended to be registered as an ``eventsys``
    ``TOUCH`` device, which turns the polled position into button-1
    MOUSEBUTTONDOWN / MOUSEMOTION / MOUSEBUTTONUP events.

    Args:
        id (str): The id of the canvas element.
    """

    def __init__(self, id):
        self.canvas = document.getElementById(id)
        self._mouse_pos = None

        # Proxy functions are required for javascript
        self.on_down = create_proxy(self._on_down)
        self.on_up = create_proxy(self._on_up)
        self.on_move = create_proxy(self._on_move)
        self.on_enter = create_proxy(self._on_enter)
        self.on_leave = create_proxy(self._on_leave)

        self.canvas.addEventListener("mousedown", self.on_down)
        self.canvas.addEventListener("mouseup", self.on_up)
        self.canvas.addEventListener("mousemove", self.on_move)
        self.canvas.addEventListener("mouseenter", self.on_enter)
        self.canvas.addEventListener("mouseleave", self.on_leave)

    def get_mouse_pos(self) -> tuple | None:
        """
        Returns the current mouse position.

        Returns:
            tuple or None: The x, y coordinates of the mouse position.
        """
        return self._mouse_pos

    def _on_down(self, e):
        if e.button == 0:  # left mouse button
            log(f"Mouse down {e.offsetX}, {e.offsetY}")
            self._mouse_pos = (e.offsetX, e.offsetY)
        else:
            return False

    def _on_up(self, e):
        if e.button == 0:  # left mouse button
            log(f"Mouse up {e.offsetX}, {e.offsetY}")
            self._mouse_pos = None
        else:
            return False

    def _on_move(self, e):
        if e.buttons & 1:
            log(f"Mouse move {e.offsetX}, {e.offsetY}")
            self._mouse_pos = (e.offsetX, e.offsetY)

    def _on_enter(self, e):
        log("Mouse enter")

    def _on_leave(self, e):
        log("Mouse leave")
        self._mouse_pos = None


class PSKeys:
    """
    Keyboard input for a PyScript canvas.

    Listens for ``keydown`` / ``keyup`` on an HTML element and queues
    ``eventsys`` ``Key`` events (with SDL-style key codes, names and modifier
    masks).  Intended to be registered as an ``eventsys`` ``QUEUE`` device via
    :meth:`read`, matching the desktop SDL2 / PyGame event stream.

    A configurable key chord emits an ``events.QUIT`` event, the equivalent of
    clicking an SDL window's close button (the broker then deinitializes the
    display and exits).  ``quit_chord`` is a ``(key_code, modifier_mask)`` tuple
    and defaults to CTRL+C; assign a different chord (e.g.
    ``(Keys.K_q, Keys.KMOD_CTRL)``) or ``None`` to disable it.  If the host
    browser/page intercepts the chosen chord, pick another one.

    Note:
        The element must be focusable and focused (e.g. clicked) to receive key
        events; the constructor sets ``tabindex`` to make the canvas focusable.

    Args:
        id (str): The id of the element to watch (usually the canvas).
    """

    def __init__(self, id):
        self.canvas = document.getElementById(id)
        try:
            self.canvas.tabIndex = 0  # make the element focusable for key events
        except Exception:
            pass

        self._queue = []
        self._pressed = set()
        self.quit_chord = (Keys.K_c, Keys.KMOD_CTRL)

        # Proxy functions are required for javascript
        self.on_keydown = create_proxy(self._on_keydown)
        self.on_keyup = create_proxy(self._on_keyup)

        self.canvas.addEventListener("keydown", self.on_keydown)
        self.canvas.addEventListener("keyup", self.on_keyup)

    def read(self):
        """
        Returns queued keyboard/quit events for an eventsys QUEUE device.

        Returns:
            list or None: The events received since the last call, or None.
        """
        if not self._queue:
            return None
        queued = self._queue
        self._queue = []
        return queued

    def _enqueue(self, type, keycode, mod):
        self._queue.append(events.Key(type, Keys.keyname(keycode), keycode, mod, 0, None))

    def _on_keydown(self, e):
        keycode = _key_to_keycode(e.key)
        mod = _mod_mask(e.ctrlKey, e.shiftKey, e.altKey, e.metaKey)
        if _chord_matches(self.quit_chord, keycode, mod):
            try:
                e.preventDefault()
            except Exception:
                pass
            self._queue.append(events.Quit(events.QUIT))
            return
        if e.repeat:  # ignore auto-repeat
            return
        self._pressed.add(keycode)
        self._enqueue(events.KEYDOWN, keycode, mod)

    def _on_keyup(self, e):
        keycode = _key_to_keycode(e.key)
        mod = _mod_mask(e.ctrlKey, e.shiftKey, e.altKey, e.metaKey)
        self._pressed.discard(keycode)
        self._enqueue(events.KEYUP, keycode, mod)


class PSDisplay(DisplayDriver):
    """
    A class to emulate a display on PyScript.

    Args:
        id (str): The id of the canvas element.
        width (int, optional): The width of the display. Defaults to None.
        height (int, optional): The height of the display. Defaults to None.
    """

    def __init__(self, id, width=None, height=None):
        self._canvas = document.getElementById(id)
        self._ctx = self._canvas.getContext("2d")
        self._width = width or self._canvas.width
        self._height = height or self._canvas.height
        self._requires_byteswap = False
        self._rotation = 0
        self.color_depth = 16

        super().__init__()

    ############### Required API Methods ################

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """
        self._canvas.width = self.width
        self._canvas.height = self.height

    def fill_rect(self, x, y, w, h, c):
        """
        Fills a rectangle with the given color.

        Args:
            x (int): The x-coordinate of the top-left corner of the rectangle.
            y (int): The y-coordinate of the top-left corner of the rectangle.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.
            c (int): The color to fill the rectangle with.

        Returns:
            (tuple): A tuple containing the x, y, w, h values
        """
        r, g, b = color_rgb(c)
        self._ctx.fillStyle = f"rgb({r},{g},{b})"
        self._ctx.fillRect(x, y, w, h)
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        """
        Blits a buffer to the display.

        Args:
            buf (bytearray): The buffer to blit.
            x (int): The x-coordinate of the top-left corner of the buffer.
            y (int): The y-coordinate of the top-left corner of the buffer.
            w (int): The width of the buffer.
            h (int): The height of the buffer.

        Returns:
            (tuple): A tuple containing the x, y, w, h values
        """
        BPP = self.color_depth // 8
        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            raise ValueError("The provided x, y, w, h values are out of range")
        if len(buf) != w * h * BPP:
            raise ValueError("The source buffer is not the correct size")
        img_data = self._ctx.createImageData(w, h)
        for i in range(0, len(buf), BPP):
            r, g, b = color_rgb(buf[i : i + BPP])
            j = i * 2
            img_data.data[j] = r
            img_data.data[j + 1] = g
            img_data.data[j + 2] = b
            img_data.data[j + 3] = 255
        self._ctx.putImageData(img_data, x, y)
        return (x, y, w, h)

    def pixel(self, x, y, c):
        """
        Sets a pixel to the given color.

        Args:
            x (int): The x-coordinate of the pixel.
            y (int): The y-coordinate of the pixel.
            c (int): The color to set the pixel to.

        Returns:
            (tuple): A tuple containing the x, y, w & h values.
        """
        return self.fill_rect(x, y, 1, 1, c)
