# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.jndisplay
"""

from io import BytesIO

from IPython.display import display, update_display
from PIL import Image, ImageDraw

from displaysys import DisplayDriver, color_rgb

_JN_TOUCH_DEPS = "pip install ipywidgets ipyevents"

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


class JNTouch:
    """
    Mouse/touch input for Jupyter Notebook via ipywidgets + ipyevents.

    Wraps the interactive ``ipywidgets`` Image that mirrors the display buffer
    and tracks the pointer position while the left mouse button is held,
    exposing it through :meth:`get_mouse_pos`.  Intended to be registered as an
    ``eventsys`` ``TOUCH`` device, which turns the polled position into button-1
    MOUSEBUTTONDOWN / MOUSEMOTION / MOUSEBUTTONUP events.

    Args:
        display_drv (JNDisplay): Display whose buffer is shown on the Image widget.
    """

    def __init__(self, display_drv):
        try:
            from ipyevents import Event
            from ipywidgets import Image, Layout, VBox
        except ImportError as exc:
            raise ImportError(
                "Jupyter touch input requires ipywidgets and ipyevents. "
                f"Install with: {_JN_TOUCH_DEPS}"
            ) from exc

        self._display_drv = display_drv
        self._mouse_pos = None
        self._png_buf = BytesIO()
        self._last_png = b""
        self._layout_wh = (0, 0)
        self._css_shown = False

        self.image = Image(format="png")
        self.image.add_class("pydisplay-jn-image")

        self._events = Event(
            source=self.image,
            watched_events=["mousedown", "mouseup", "mousemove", "mouseleave"],
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

    def get_mouse_pos(self):
        """
        Returns the current mouse position in display coordinates.

        Returns:
            tuple or None: (x, y) while the left button is pressed, else None.
        """
        return self._mouse_pos

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

    def _on_dom_event(self, event):
        kind = event.get("type")
        if kind == "mousedown" and event.get("button", 0) == 0:
            if "dataX" not in event or "dataY" not in event:
                return
            self._mouse_pos = (int(event["dataX"]), int(event["dataY"]))
        elif kind == "mousemove" and event.get("buttons", 0) & 1:
            self._mouse_pos = (int(event["dataX"]), int(event["dataY"]))
        elif kind in ("mouseup", "mouseleave"):
            self._mouse_pos = None


class JNDisplay(DisplayDriver):
    """
    A class to emulate a display on Jupyter Notebook.

    Args:
        width (int): The width of the display.
        height (int): The height of the display.

    Attributes:
        color_depth (int): The color depth of the display
    """

    _next_display_id = 0

    def __init__(self, width, height):
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

        super().__init__(auto_refresh=True)

    ############### Required API Methods ################

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """
        if self._jn_devices is not None:
            self._buffer = Image.new("RGB", (self.width, self.height))
            self._draw = ImageDraw.Draw(self._buffer)
            self._jn_devices._last_png = b""
            self._jn_devices.update_buffer(self._buffer)
        # Static PIL output is deferred to show() so touch mode only gets one widget.

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
        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            raise ValueError("The provided x, y, w, h values are out of range")
        if len(buf) != w * h * BPP:
            raise ValueError("The source buffer is not the correct size")

        for j in range(h):
            for i in range(w):
                color = buf[(j * w + i) * BPP : (j * w + i) * BPP + BPP]
                self.pixel(x + i, y + j, color)
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

    ############### Optional API Methods ################

    def show(self, _timer=None) -> None:
        """
        Updates the display with the current buffer.
        """
        if self._jn_devices is not None:
            self._jn_devices.update_buffer(self._buffer)
        elif not self._static_shown:
            if _timer is not None:
                # Auto-refresh timer fired before a device or explicit show().
                # Creating a static output here would duplicate the interactive
                # widget that JNTouch is about to display.  Wait for an
                # explicit show() (non-interactive use) or device attach.
                return
            display(self._buffer, display_id=self._display_id)
            self._static_shown = True
        else:
            update_display(self._buffer, display_id=self._display_id)
