# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.psdisplay
"""

from displaysys import DisplayDriver, color_rgb
from pyscript.ffi import create_proxy
from js import document, console


def log(*args):
    console.log(*args)


class PSDevices:
    """
    A class to emulate a display on PyScript.

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
