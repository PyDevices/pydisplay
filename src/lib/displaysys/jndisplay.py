# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.jndisplay
"""

from io import BytesIO

from IPython.display import display, update_display
from PIL import Image, ImageDraw

from displaysys import DisplayDriver, color_rgb, default_quit_chord
from eventsys import events
from eventsys.keys import Keys, key_to_keycode, mod_mask

_JN_DEPS = "pip install ipywidgets ipyevents"

_CSS_DISPLAY_ID = "pydisplay_jn_styles"


def _inject_notebook_css(width, height, first_time):
    """Shrink VS Code/Cursor ipywidget output chrome; size the Image DOM node."""
    from IPython.display import HTML, display, update_display

    css = HTML(
        f"""<style>
.cell-output-ipywidget-background {{
    background: transparent !important;
    width: fit-content !important;
    max-width: fit-content !important;
    display: inline-block !important;
}}
.pydisplay-jn-image {{
    width: {width}px !important;
    height: {height}px !important;
    max-width: {width}px !important;
    max-height: {height}px !important;
    background: #000 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    line-height: 0 !important;
}}
.pydisplay-jn-image img {{
    width: {width}px !important;
    height: {height}px !important;
    object-fit: fill !important;
    display: block !important;
}}
</style>"""
    )
    if first_time:
        display(css, display_id=_CSS_DISPLAY_ID)
    else:
        update_display(css, display_id=_CSS_DISPLAY_ID)


def _buttons_tuple(buttons):
    """Convert a DOM ``buttons`` bitmask to an (left, middle, right) tuple."""
    return (
        1 if buttons & 1 else 0,  # left
        1 if buttons & 4 else 0,  # middle
        1 if buttons & 2 else 0,  # right
    )


class JNDevices:
    """
    Unified input for Jupyter Notebook, registered as an eventsys QUEUE device.

    Creates the interactive ``ipywidgets`` Image that mirrors the display buffer
    and watches it (via ``ipyevents``) for all available input, turning it into
    ``eventsys.events`` objects (matching the desktop SDL2 / PyGame event
    stream), drained through :meth:`read`:

    - **Mouse**: ``MOUSEMOTION`` on every move, ``MOUSEBUTTONDOWN`` /
      ``MOUSEBUTTONUP`` for any button.
    - **Wheel**: ``MOUSEWHEEL`` (also consumed by encoder devices).
    - **Keyboard**: ``KEYDOWN`` / ``KEYUP`` with SDL-style key codes, names and
      modifier masks (left/right modifier variants via key location).

    Quit chord handling is configured on :class:`JNDisplay` via ``quit_chord``
    (default CTRL+Q); :class:`eventsys.QueueDevice` applies it when ``data=``
    is the display driver.

    This class also owns the display widget: ``JNDisplay`` pushes frames to it
    via :meth:`update_buffer`.

    Note:
        The Image widget must be focused (e.g. clicked) to receive key events,
        and some keys may be consumed by the notebook front end (JupyterLab /
        classic Notebook / VS Code) before they reach the widget.

    Args:
        display_drv (JNDisplay): Display whose buffer is shown on the Image widget.
    """

    def __init__(self, display_drv):
        try:
            from ipyevents import Event
            from ipywidgets import Image, Layout, VBox
        except ImportError as exc:
            raise ImportError(
                f"Jupyter input requires ipywidgets and ipyevents. Install with: {_JN_DEPS}"
            ) from exc

        self._display_drv = display_drv
        self._png_buf = BytesIO()
        self._last_png = b""
        self._layout_wh = (0, 0)
        self._css_shown = False

        self._queue = []
        self._pressed = set()

        self.image = Image(format="png")
        self.image.add_class("pydisplay-jn-image")

        self._events = Event(
            source=self.image,
            watched_events=[
                "mousedown",
                "mouseup",
                "mousemove",
                "wheel",
                "keydown",
                "keyup",
            ],
        )
        self._events.on_dom_event(self._on_dom_event)

        display_drv._jn_devices = self
        self._sync_widget_size()
        _inject_notebook_css(display_drv.width, display_drv.height, not self._css_shown)
        self._css_shown = True
        self.update_buffer(display_drv._buffer)

        w, h = display_drv.width, display_drv.height
        self._root = VBox(
            [self.image, self._events],
            layout=Layout(
                width=f"{w}px",
                height=f"{h}px",
                padding="0",
                margin="0",
                overflow="hidden",
            ),
        )
        display(self._root)

    def read(self):
        """
        Returns queued input events for an eventsys QUEUE device.

        Returns:
            list or None: The events received since the last call, or None.
        """
        if not self._queue:
            return None
        queued = self._queue
        self._queue = []
        return queued

    def update_buffer(self, pil_image):
        """Push a PIL image to the interactive widget."""
        drv = self._display_drv
        if (drv.width, drv.height) != self._layout_wh:
            self._sync_widget_size()
        self._png_buf.seek(0)
        self._png_buf.truncate()
        pil_image.save(self._png_buf, format="PNG")
        png = self._png_buf.getvalue()
        if png == self._last_png:
            return
        self._last_png = png
        self.image.value = png

    def _sync_widget_size(self):
        drv = self._display_drv
        w, h = drv.width, drv.height
        self._layout_wh = (w, h)
        px, py = f"{w}px", f"{h}px"
        self.image.layout.width = px
        self.image.layout.height = py
        self.image.layout.min_width = px
        self.image.layout.max_width = px
        self.image.layout.min_height = py
        self.image.layout.max_height = py
        self.image.layout.object_fit = "fill"
        self.image.layout.margin = "0"
        self.image.layout.padding = "0"
        self.image.layout.background_color = "#000000"
        if self._css_shown:
            _inject_notebook_css(w, h, False)
        if hasattr(self, "_root"):
            root = self._root.layout
            root.width = px
            root.height = py

    ############### Event handling ################

    def _on_dom_event(self, event):
        kind = event.get("type")
        if kind == "mousemove":
            self._on_mouse_move(event)
        elif kind == "mousedown":
            self._on_mouse_button(event, events.MOUSEBUTTONDOWN)
        elif kind == "mouseup":
            self._on_mouse_button(event, events.MOUSEBUTTONUP)
        elif kind == "wheel":
            self._on_wheel(event)
        elif kind in ("keydown", "keyup"):
            self._on_key(event, kind)

    def _pos(self, event):
        return (int(event.get("dataX", 0)), int(event.get("dataY", 0)))

    def _on_mouse_button(self, event, type):
        self._queue.append(
            events.Button(type, self._pos(event), event.get("button", 0) + 1, False, None)
        )

    def _on_mouse_move(self, event):
        rel = (int(event.get("movementX", 0)), int(event.get("movementY", 0)))
        self._queue.append(
            events.Motion(
                events.MOUSEMOTION,
                self._pos(event),
                rel,
                _buttons_tuple(event.get("buttons", 0)),
                False,
                None,
            )
        )

    def _on_wheel(self, event):
        dx = event.get("deltaX", 0)
        dy = event.get("deltaY", 0)
        # DOM deltaY > 0 means scrolling down; SDL/PyGame report up as positive.
        x = -1 if dx < 0 else (1 if dx > 0 else 0)
        y = 1 if dy < 0 else (-1 if dy > 0 else 0)
        self._queue.append(events.Wheel(events.MOUSEWHEEL, False, x, y, dx, dy, False, None))

    def _on_key(self, event, kind):
        keycode = key_to_keycode(event.get("key", ""), event.get("location", 0))
        mod = mod_mask(
            event.get("ctrlKey"),
            event.get("shiftKey"),
            event.get("altKey"),
            event.get("metaKey"),
        )
        if kind == "keydown":
            if event.get("repeat"):  # ignore auto-repeat
                return
            self._pressed.add(keycode)
            self._enqueue_key(events.KEYDOWN, keycode, mod)
        else:
            self._pressed.discard(keycode)
            self._enqueue_key(events.KEYUP, keycode, mod)

    def _enqueue_key(self, type, keycode, mod):
        self._queue.append(events.Key(type, Keys.keyname(keycode), keycode, mod, 0, None))


class JNDisplay(DisplayDriver):
    needs_refresh = True

    """
    A class to emulate a display on Jupyter Notebook.

    Supports ILI9341-style vertical scroll emulation (same band compositing as
    SDL/PG/PS). Interactive output uses :class:`JNDevices`; static notebooks can
    call :meth:`show` without a device.

    Args:
        width (int): The width of the display.
        height (int): The height of the display.

    Attributes:
        color_depth (int): The color depth of the display
        touch_scale (float): Pointer scale for ``QueueDevice`` (always ``1.0``).
        quit_chord: Keyboard chord for quit (default CTRL+Q); ``None`` disables.
    """

    _next_display_id = 0

    def __init__(self, width, height, *, quiet=False):
        self._display_id = f"JNDisplay_{JNDisplay._next_display_id}"
        JNDisplay._next_display_id += 1
        self._width = width
        self._height = height
        self._requires_byteswap = False
        self._rotation = 0
        self.color_depth = 16
        self._buffer = Image.new("RGB", (self.width, self.height))
        self._draw = ImageDraw.Draw(self._buffer)
        self._jn_devices = None
        self._static_shown = False
        self.touch_scale = 1.0
        self.quit_chord = default_quit_chord()
        self._visible = None

        super().__init__(quiet=quiet)

    ############### Required API Methods ################

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """
        if self._jn_devices is not None:
            self._buffer = Image.new("RGB", (self.width, self.height))
            self._draw = ImageDraw.Draw(self._buffer)
            self._jn_devices._last_png = b""
            self._jn_devices.update_buffer(self.render())
        else:
            super().vscrdef(0, self.height, 0)
            self.vscsad(False)
            self._visible = None

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
        color = c & 0xFFFF
        r, g, b = color_rgb(color)
        x2 = x + w
        y2 = y + h
        top = min(y, y2)
        left = min(x, x2)
        bottom = max(y, y2)
        right = max(x, x2)
        self._draw.rectangle([(left, top), (right, bottom)], fill=(r, g, b))
        self.render((x, y, w, h))
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        """
        Blits a buffer to the display at the given coordinates.

        Args:
            buf (bytearray): The buffer to blit to the display.
            x (int): The x-coordinate of the top-left corner of the buffer.
            y (int): The y-coordinate of the top-left corner of the buffer.
            w (int): The width of the buffer.
            h (int): The height of the buffer.

        Returns:
            (tuple): A tuple containing the x, y, w, h values.
        """

        BPP = self.color_depth // 8
        if len(buf) != w * h * BPP:
            raise ValueError("The source buffer is not the correct size")

        src_w = w
        src_x0 = 0
        src_y0 = 0
        if x < 0:
            src_x0 = -x
            w += x
            x = 0
        if y < 0:
            src_y0 = -y
            h += y
            y = 0
        if x + w > self.width:
            w = self.width - x
        if y + h > self.height:
            h = self.height - y
        if w <= 0 or h <= 0:
            return (x, y, w, h)

        for j in range(h):
            for i in range(w):
                color = buf[
                    ((src_y0 + j) * src_w + src_x0 + i) * BPP : ((src_y0 + j) * src_w + src_x0 + i)
                    * BPP
                    + BPP
                ]
                self.pixel(x + i, y + j, color)
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
            (tuple): A tuple containing the x, y, w and h values.
        """
        r, g, b = color_rgb(c)
        self._draw.point((x, y), fill=(r, g, b))
        return (x, y, 1, 1)

    ############### Scrolling (ILI9341-style, like PG/PS/SDL) ################

    def vscrdef(self, tfa: int, vsa: int, bfa: int) -> None:
        super().vscrdef(tfa, vsa, bfa)
        self.render()

    def vscsad(self, vssa=None) -> int:
        if vssa is not None:
            super().vscsad(vssa)
            self.render()
        return self._vssa

    def render(self, render_rect=None):
        """Composite offscreen buffer to visible frame, applying vertical scroll."""
        y_start = self.vscsad()
        if not y_start:
            return self._buffer

        w, h = self.width, self.height
        if self._visible is None or self._visible.size != (w, h):
            self._visible = Image.new("RGB", (w, h))

        tfa = self._tfa
        vsa = self._vsa
        bfa = self._bfa
        buf = self._buffer
        vis = self._visible

        if tfa > 0:
            vis.paste(buf.crop((0, 0, w, tfa)), (0, 0))

        vsa_top_height = vsa + tfa - y_start
        vis.paste(buf.crop((0, y_start, w, y_start + vsa_top_height)), (0, tfa))

        vsa_btm_height = vsa - vsa_top_height
        vis.paste(buf.crop((0, tfa, w, tfa + vsa_btm_height)), (0, tfa + vsa_top_height))

        if bfa > 0:
            vis.paste(buf.crop((0, tfa + vsa, w, tfa + vsa + bfa)), (0, tfa + vsa))

        return vis

    ############### Optional API Methods ################

    def show(self, _timer=None) -> None:
        """
        Updates the display with the current buffer.
        """
        frame = self.render()
        if self._jn_devices is not None:
            self._jn_devices.update_buffer(frame)
        elif not self._static_shown:
            if _timer is not None:
                # Auto-refresh timer fired before a device or explicit show().
                # Creating a static output here would duplicate the interactive
                # widget that JNDevices is about to display.  Wait for an
                # explicit show() (non-interactive use) or device attach.
                return
            display(frame, display_id=self._display_id)
            self._static_shown = True
        else:
            update_display(frame, display_id=self._display_id)
