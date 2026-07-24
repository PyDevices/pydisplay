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
from eventsys.keys import Keys, default_quit_chord, dom_key_scrolls_page, key_to_keycode, mod_mask

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

    Quit chord handling is configured on :class:`PSDisplay` via ``quit_chord``
    (default from :func:`eventsys.keys.default_quit_chord`, CTRL+Q).
    :class:`~eventsys.HostEventsDevice` applies the chord and Android Back
    (``K_AC_BACK``) when constructed with ``display=``.

    Note:
        The element must be focused to receive key events.  The constructor sets
        ``tabindex`` and calls :meth:`_focus_canvas` so keyboard input goes to the
        game; pointer down on the canvas refocuses it.

    Args:
        id (str): The id of the element to watch (usually the canvas).
        display (PSDisplay, optional): Pass the same ``PSDisplay`` used as
            ``QueueDevice`` ``data`` (for ``touch_scale`` pointer mapping).
    """

    def __init__(self, id, display=None):
        self.canvas = document.getElementById(id)
        self._display = display
        try:
            self.canvas.tabIndex = 0  # make the element focusable for key events
            self.canvas.style.touchAction = "none"  # don't scroll/zoom on touch
        except Exception:
            pass

        self._queue = []
        self._pressed = set()

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
        self._focus_canvas()

    def _focus_canvas(self):
        """Move keyboard focus to the canvas so keys reach the game, not the page."""
        try:
            self.canvas.focus()
        except Exception:
            pass

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

    def _map_pos(self, x, y):
        try:
            return (int(x), int(y))
        except Exception:
            return (int(float(x)), int(float(y)))

    def _map_rel(self, dx, dy):
        try:
            return (int(dx), int(dy))
        except Exception:
            return (int(float(dx)), int(float(dy)))

    def _on_pointer_down(self, e):
        self._focus_canvas()
        try:
            self.canvas.setPointerCapture(e.pointerId)
        except Exception:
            pass
        self._queue.append(
            events.Button(
                events.MOUSEBUTTONDOWN,
                self._map_pos(e.offsetX, e.offsetY),
                e.button + 1,  # DOM 0/1/2 -> SDL 1/2/3
                self._is_touch(e),
                None,
            )
        )

    def _on_pointer_up(self, e):
        self._queue.append(
            events.Button(
                events.MOUSEBUTTONUP,
                self._map_pos(e.offsetX, e.offsetY),
                e.button + 1,
                self._is_touch(e),
                None,
            )
        )

    def _on_pointer_move(self, e):
        self._queue.append(
            events.Motion(
                events.MOUSEMOTION,
                self._map_pos(e.offsetX, e.offsetY),
                self._map_rel(e.movementX, e.movementY),
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

    def _suppress_browser_scroll(self, e, keycode):
        if dom_key_scrolls_page(keycode):
            try:
                e.preventDefault()
            except Exception:
                pass

    def _on_keydown(self, e):
        keycode = key_to_keycode(e.key, e.location)
        mod = mod_mask(e.ctrlKey, e.shiftKey, e.altKey, e.metaKey)
        self._suppress_browser_scroll(e, keycode)
        if e.repeat:  # ignore auto-repeat
            return
        self._pressed.add(keycode)
        self._enqueue_key(events.KEYDOWN, keycode, mod)

    def _on_keyup(self, e):
        keycode = key_to_keycode(e.key, e.location)
        mod = mod_mask(e.ctrlKey, e.shiftKey, e.altKey, e.metaKey)
        self._suppress_browser_scroll(e, keycode)
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
    needs_refresh = True

    """
    A class to emulate a display on PyScript.

    Args:
        id (str): The id of the canvas element.
        width (int, optional): The width of the display. Defaults to None.
        height (int, optional): The height of the display. Defaults to None.
    """

    def __init__(self, id, width=None, height=None, *, quiet=False):
        self._canvas = document.getElementById(id)
        self._vis_ctx = self._canvas.getContext("2d")
        self._buffer = None
        self._buf_ctx = None
        self._width = width or self._canvas.width
        self._height = height or self._canvas.height
        self._requires_byteswap = False
        self._rotation = 0
        self.color_depth = 16
        self.quit_chord = default_quit_chord()
        self.touch_scale = 1.0

        super().__init__(quiet=quiet)

    ############### Required API Methods ################

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """
        self._canvas.width = self.width
        self._canvas.height = self.height
        if self._buffer is None:
            self._buffer = document.createElement("canvas")
            self._buf_ctx = self._buffer.getContext("2d")
        self._buffer.width = self.width
        self._buffer.height = self.height
        if getattr(self, "_rgba_lut", None) is None:
            lut = bytearray(65536 * 4)
            for v in range(65536):
                lo, hi = v & 0xFF, v >> 8
                k = v << 2
                lut[k] = (hi & 0xF8) | ((hi >> 5) & 0x07)
                lut[k + 1] = ((hi << 5) & 0xE0) | ((lo >> 3) & 0x1F)
                lut[k + 2] = ((lo << 3) & 0xF8) | ((lo >> 2) & 0x07)
                lut[k + 3] = 255
            self._rgba_lut = lut
        sx, _sy = self._pointer_scale()
        self.touch_scale = sx
        # Match PGDisplay / SDLDisplay / JNDisplay: default full-height scroll region
        # so vscsad() works before an explicit set_vscroll/vscrdef.
        super().vscrdef(0, self.height, 0)
        self._vssa = False

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
        self._buf_ctx.fillStyle = f"rgb({r},{g},{b})"
        self._buf_ctx.fillRect(x, y, w, h)
        self.render((x, y, w, h))
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
        lut = self._rgba_lut
        if lut is None:
            self.init()
            lut = self._rgba_lut
        img_data = self._buf_ctx.createImageData(w, h)
        data = img_data.data
        j = 0
        for i in range(0, len(buf), BPP):
            k = (buf[i] | (buf[i + 1] << 8)) << 2
            data[j] = lut[k]
            data[j + 1] = lut[k + 1]
            data[j + 2] = lut[k + 2]
            data[j + 3] = lut[k + 3]
            j += 4
        self._buf_ctx.putImageData(img_data, x, y)
        self.render((x, y, w, h))
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

    ############### Scrolling (ILI9341-style, like SDLDisplay / PGDisplay) ################

    def vscrdef(self, tfa: int, vsa: int, bfa: int) -> None:
        super().vscrdef(tfa, vsa, bfa)
        self.render()

    def vscsad(self, vssa=None) -> int:
        if vssa is not None:
            super().vscsad(vssa)
            self.render()
        return self._vssa

    def render(self, render_rect=None) -> None:
        """Copy the offscreen buffer to the visible canvas, applying vertical scroll."""
        buf = self._buffer
        vis = self._vis_ctx
        w, h = self.width, self.height
        y_start = self.vscsad()
        if not y_start:
            if render_rect is not None:
                x, y, rw, rh = render_rect
                vis.drawImage(buf, x, y, rw, rh, x, y, rw, rh)
            else:
                vis.drawImage(buf, 0, 0, w, h, 0, 0, w, h)
            return

        tfa = self._tfa
        vsa = self._vsa
        bfa = self._bfa
        if tfa > 0:
            vis.drawImage(buf, 0, 0, w, tfa, 0, 0, w, tfa)

        vsa_top_height = vsa + tfa - y_start
        vis.drawImage(buf, 0, y_start, w, vsa_top_height, 0, tfa, w, vsa_top_height)

        vsa_btm_height = vsa - vsa_top_height
        vis.drawImage(buf, 0, tfa, w, vsa_btm_height, 0, tfa + vsa_top_height, w, vsa_btm_height)

        if bfa > 0:
            vis.drawImage(buf, 0, tfa + vsa, w, bfa, 0, tfa + vsa, w, bfa)

    def show(self, _timer=None) -> None:
        self.render()

    def _pointer_scale(self):
        """Framebuffer pixels per CSS layout pixel (1.0 when layout is 1:1)."""
        rect = self._canvas.getBoundingClientRect()
        rw, rh = float(rect.width), float(rect.height)
        if rw <= 0 or rh <= 0:
            return 1.0, 1.0
        return float(self._canvas.width) / rw, float(self._canvas.height) / rh

    def map_pointer(self, local_x, local_y):
        """
        Map element-local pointer coordinates to framebuffer ``(x, y)``.

        ``PSDevices`` maps coordinates at capture time when constructed with a
        ``PSDisplay``; ``QueueDevice`` forwards events unchanged.
        """
        sx, sy = self._pointer_scale()
        return (int(float(local_x) * sx), int(float(local_y) * sy))

    def map_pointer_rel(self, dx, dy):
        """Map a DOM pointer delta (``movementX``/``movementY``) to framebuffer pixels."""
        sx, sy = self._pointer_scale()
        return (int(float(dx) * sx), int(float(dy) * sy))
