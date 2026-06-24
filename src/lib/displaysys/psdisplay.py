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
from eventsys.keys import Keys, chord_matches, key_to_keycode, mod_mask

try:  # Gamepad polling is optional and only available in a browser.
    from js import navigator
except ImportError:
    navigator = None


def log(*args):
    console.log(*args)


def _buttons_tuple(buttons):
    """Convert a DOM ``buttons`` bitmask to an (left, middle, right) tuple."""
    return (
        1 if buttons & 1 else 0,  # left
        1 if buttons & 4 else 0,  # middle
        1 if buttons & 2 else 0,  # right
    )


class PSDevices:
    """
    Unified input for a PyScript canvas, registered as an eventsys QUEUE device.

    Captures all available browser input on a single HTML element and turns it
    into ``eventsys.events`` objects (matching the desktop SDL2 / PyGame event
    stream), drained through :meth:`read`:

    - **Pointer** (mouse, touch and pen via Pointer Events): ``MOUSEMOTION`` on
      every move, ``MOUSEBUTTONDOWN`` / ``MOUSEBUTTONUP`` for any button, with
      the ``touch`` flag set for non-mouse pointers.
    - **Wheel**: ``MOUSEWHEEL`` (also consumed by encoder devices).
    - **Keyboard**: ``KEYDOWN`` / ``KEYUP`` with SDL-style key codes, names and
      modifier masks (left/right modifier variants via key location).
    - **Gamepad** (Gamepad API, polled on each :meth:`read`): ``JOYAXISMOTION``,
      ``JOYBUTTONDOWN`` / ``JOYBUTTONUP``.
    - **Quit**: an assignable key chord emits ``events.QUIT`` (the equivalent of
      clicking an SDL window's close button; the broker then deinitializes the
      display and exits).  ``quit_chord`` is a ``(key_code, modifier_mask)``
      tuple defaulting to CTRL+C; assign another (e.g.
      ``(Keys.K_q, Keys.KMOD_CTRL)``) or ``None`` to disable.  If the host
      browser/page intercepts the chord, pick a different one.

    Note:
        The element must be focused (e.g. clicked) to receive key events; the
        constructor sets ``tabindex`` to make the canvas focusable.

    Args:
        id (str): The id of the element to watch (usually the canvas).
    """

    def __init__(self, id):
        self.canvas = document.getElementById(id)
        try:
            self.canvas.tabIndex = 0  # make the element focusable for key events
            self.canvas.style.touchAction = "none"  # don't scroll/zoom on touch
        except Exception:
            pass

        self._queue = []
        self._pressed = set()
        self.quit_chord = (Keys.K_c, Keys.KMOD_CTRL)

        # Gamepad state keyed by gamepad index: (axes list, pressed-bool list).
        self._gp_axes = {}
        self._gp_buttons = {}

        # Proxy functions are required for javascript
        self._proxies = {
            "pointerdown": create_proxy(self._on_pointer_down),
            "pointerup": create_proxy(self._on_pointer_up),
            "pointermove": create_proxy(self._on_pointer_move),
            "wheel": create_proxy(self._on_wheel),
            "contextmenu": create_proxy(self._on_contextmenu),
            "keydown": create_proxy(self._on_keydown),
            "keyup": create_proxy(self._on_keyup),
        }
        for name, proxy in self._proxies.items():
            self.canvas.addEventListener(name, proxy)

    def read(self):
        """
        Returns queued input events for an eventsys QUEUE device.

        Polls connected gamepads (if any) and returns all events received since
        the last call.

        Returns:
            list or None: The events, or None if there were none.
        """
        self._poll_gamepads()
        if not self._queue:
            return None
        queued = self._queue
        self._queue = []
        return queued

    ############### Pointer (mouse / touch / pen) ################

    def _is_touch(self, e):
        try:
            return e.pointerType != "mouse"
        except Exception:
            return False

    def _on_pointer_down(self, e):
        try:
            self.canvas.setPointerCapture(e.pointerId)
        except Exception:
            pass
        self._queue.append(
            events.Button(
                events.MOUSEBUTTONDOWN,
                (e.offsetX, e.offsetY),
                e.button + 1,  # DOM 0/1/2 -> SDL 1/2/3
                self._is_touch(e),
                None,
            )
        )

    def _on_pointer_up(self, e):
        self._queue.append(
            events.Button(
                events.MOUSEBUTTONUP,
                (e.offsetX, e.offsetY),
                e.button + 1,
                self._is_touch(e),
                None,
            )
        )

    def _on_pointer_move(self, e):
        self._queue.append(
            events.Motion(
                events.MOUSEMOTION,
                (e.offsetX, e.offsetY),
                (e.movementX, e.movementY),
                _buttons_tuple(e.buttons),
                self._is_touch(e),
                None,
            )
        )

    def _on_wheel(self, e):
        try:
            e.preventDefault()
        except Exception:
            pass
        # DOM deltaY > 0 means scrolling down; SDL/PyGame report up as positive.
        x = -1 if e.deltaX < 0 else (1 if e.deltaX > 0 else 0)
        y = 1 if e.deltaY < 0 else (-1 if e.deltaY > 0 else 0)
        self._queue.append(
            events.Wheel(events.MOUSEWHEEL, False, x, y, e.deltaX, e.deltaY, False, None)
        )

    def _on_contextmenu(self, e):
        # Suppress the browser menu so right-click is usable as a button event.
        try:
            e.preventDefault()
        except Exception:
            pass

    ############### Keyboard ################

    def _enqueue_key(self, type, keycode, mod):
        self._queue.append(events.Key(type, Keys.keyname(keycode), keycode, mod, 0, None))

    def _on_keydown(self, e):
        keycode = key_to_keycode(e.key, e.location)
        mod = mod_mask(e.ctrlKey, e.shiftKey, e.altKey, e.metaKey)
        if chord_matches(self.quit_chord, keycode, mod):
            try:
                e.preventDefault()
            except Exception:
                pass
            self._queue.append(events.Quit(events.QUIT))
            return
        if e.repeat:  # ignore auto-repeat
            return
        self._pressed.add(keycode)
        self._enqueue_key(events.KEYDOWN, keycode, mod)

    def _on_keyup(self, e):
        keycode = key_to_keycode(e.key, e.location)
        mod = mod_mask(e.ctrlKey, e.shiftKey, e.altKey, e.metaKey)
        self._pressed.discard(keycode)
        self._enqueue_key(events.KEYUP, keycode, mod)

    ############### Gamepad ################

    def _poll_gamepads(self):
        if navigator is None:
            return
        try:
            pads = navigator.getGamepads()
        except Exception:
            return
        for i in range(pads.length):
            pad = pads[i]
            if not pad:
                continue
            gid = pad.index

            axes = pad.axes
            cur_axes = [float(axes[a]) for a in range(axes.length)]
            prev_axes = self._gp_axes.get(gid, [0.0] * len(cur_axes))
            for a in range(len(cur_axes)):
                prev = prev_axes[a] if a < len(prev_axes) else 0.0
                if cur_axes[a] != prev:
                    self._queue.append(
                        events.JoyAxisMotion(events.JOYAXISMOTION, gid, a, cur_axes[a])
                    )
            self._gp_axes[gid] = cur_axes

            btns = pad.buttons
            cur_btns = [bool(btns[b].pressed) for b in range(btns.length)]
            prev_btns = self._gp_buttons.get(gid, [False] * len(cur_btns))
            for b in range(len(cur_btns)):
                prev = prev_btns[b] if b < len(prev_btns) else False
                if cur_btns[b] != prev:
                    if cur_btns[b]:
                        self._queue.append(events.JoyButtonDown(events.JOYBUTTONDOWN, gid, b))
                    else:
                        self._queue.append(events.JoyButtonUp(events.JOYBUTTONUP, gid, b))
            self._gp_buttons[gid] = cur_btns


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
