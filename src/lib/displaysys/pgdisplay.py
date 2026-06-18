# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.pgdisplay
"""

import pygame as pg

from displaysys import DisplayDriver, color_rgb


def poll():
    """
    Polls for an event and returns the event type and data.

    Returns:
        Optional[pg.event.Event | False]: The event type and data.
    """
    return pg.event.poll()


def get() -> [pg.event.Event]:
    """
    Gets all events from the event queue.

    Returns:
        [pg.event.Event]: A list of events.
    """
    return pg.event.get()


class PGDisplay(DisplayDriver):
    """
    A class to emulate an LCD using pygame.
    Provides scrolling and rotation functions similar to an LCD.  The .texture
    object functions as the LCD's internal memory.

    Args:
        width (int, optional): The width of the display. Defaults to 320.
        height (int, optional): The height of the display. Defaults to 240.
        rotation (int, optional): The rotation of the display. Defaults to 0.
        color_depth (int, optional): The color depth of the display. Defaults to 16.
        title (str, optional): The title of the display window. Defaults to "displaysys".
        scale (float, optional): The scale of the display. Defaults to 1.0.
        window_flags (int, optional): The flags for creating the display window. Defaults to pg.SHOWN

    Attributes:
        color_depth (int): The color depth of the display.
        touch_scale (float): The touch scale of the display.
    """

    def __init__(
        self,
        width=320,
        height=240,
        rotation=0,
        color_depth=16,
        title="displaysys",
        scale=1.0,
        window_flags=pg.SHOWN,
    ):
        self._width = width
        self._height = height
        self._rotation = rotation
        self.color_depth = color_depth
        self._title = title
        self._window_flags = window_flags
        self._scale = scale
        self.touch_scale = scale
        self._buffer = None
        self._requires_byteswap = False

        self._bytes_per_pixel = color_depth // 8

        if self._scale != 1 and not hasattr(pg.transform, "scale_by"):
            print(
                f"PGDisplay:  Scaling is set to {self._scale}, but pygame {pg.ver} does not support it."
            )
            self._scale = 1

        pg.init()

        self._buffer = pg.Surface(size=(self._width, self._height), depth=self.color_depth)
        self._buffer.fill((0, 0, 0))

        super().__init__(auto_refresh=True)

    ############### Required API Methods ################

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """
        self._window = pg.display.set_mode(
            size=(int(self.width * self._scale), int(self.height * self._scale)),
            flags=self._window_flags,
            depth=self.color_depth,
            display=0,
            vsync=0,
        )
        pg.display.set_caption(self._title)

        super().vscrdef(
            0, self.height, 0
        )  # Set the vertical scroll definition without calling show
        self.vscsad(False)  # Scroll offset; set to False to disable scrolling

    def blit_rect(self, buffer: memoryview, x: int, y: int, w: int, h: int):
        """
        Blits a buffer to the display.

        Args:
            buffer (memoryview): The buffer to blit.
            x (int): The x-coordinate of the buffer.
            y (int): The y-coordinate of the buffer.
            w (int): The width to blit.
            h (int): The height to blit.

        Returns:
            (tuple): A tuple containing the x, y, w, h values.
        """

        blitRect = pg.Rect(x, y, w, h)
        for i in range(h):
            for j in range(w):
                pixel_index = (i * w + j) * self._bytes_per_pixel
                color = color_rgb(buffer[pixel_index : pixel_index + self._bytes_per_pixel])
                self._buffer.set_at((x + j, y + i), color)
        self.render(blitRect)
        return (x, y, w, h)

    def fill_rect(self, x: int, y: int, w: int, h: int, c: int):
        """
        Fill a rectangle with a color.

        Renders to the texture instead of directly to the window
        to facilitate scrolling and scaling.

        Args:
            x (int): The x-coordinate of the rectangle.
            y (int): The y-coordinate of the rectangle.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.
            c (int): The color of the rectangle.

        Returns:
            (tuple): A tuple containing the x, y, w, h values.
        """
        fillRect = pg.Rect(x, y, w, h)
        self._buffer.fill(color_rgb(c), fillRect)
        self.render(fillRect)
        return (x, y, w, h)

    def pixel(self, x: int, y: int, c: int):
        """
        Set a pixel on the display.

        Args:
            x (int): The x-coordinate of the pixel.
            y (int): The y-coordinate of the pixel.
            c (int): The color of the pixel.

        Returns:
            (tuple): A tuple containing the x, y, w & h values.
        """
        return self.blit_rect(bytearray(c.to_bytes(2, "little")), x, y, 1, 1)

    ############### API Method Overrides ################

    def vscrdef(self, tfa: int, vsa: int, bfa: int) -> None:
        """
        Set the vertical scroll definition.

        Args:
            tfa (int): The top fixed area.
            vsa (int): The vertical scroll area.
            bfa (int): The bottom fixed area.
        """
        super().vscrdef(tfa, vsa, bfa)
        self.render()

    def vscsad(self, vssa=None) -> int:
        """
        Set the vertical scroll start address.

        Args:
            vssa (Optional[int], optional): The vertical scroll start address. Defaults to None.

        Returns:
            int: The vertical scroll start address.
        """
        if vssa is not None:
            super().vscsad(vssa)
            self.render()
        return self._vssa

    def _rotation_helper(self, value):
        """
        Helper function for the rotation setter.
        """
        if (angle := (value % 360) - (self._rotation % 360)) != 0:
            tempBuffer = pg.transform.rotate(self._buffer, -angle)
            self._buffer = tempBuffer

    ############### Class Specific Methods ##############

    def render(self, renderRect=None) -> None:
        """
        Render the display.  Automatically called after blitting or filling the display.

        Args:
            renderRect (Optional[pg.Rect], optional): The rectangle to render. Defaults to None.
        """
        s = self._scale
        buffer = pg.transform.scale_by(self._buffer, s) if s != 1 else self._buffer
        if not (y_start := self.vscsad()):
            if renderRect is not None:
                x, y, w, h = renderRect
                renderRect = pg.Rect(x * s, y * s, w * s, h * s)
                dest = renderRect
            else:
                dest = (0, 0)
            self._window.blit(buffer, dest, renderRect)
        else:
            # Ignore renderRect and render the entire buffer to the window in four steps
            y_start *= s
            tfa = self._tfa * s
            vsa = self._vsa * s
            bfa = self._bfa * s
            width = self.width * s

            if tfa > 0:
                tfaRect = pg.Rect(0, 0, width, tfa)
                self._window.blit(buffer, tfaRect, tfaRect)

            vsaTopHeight = vsa + tfa - y_start
            vsaTopSrcRect = pg.Rect(0, y_start, width, vsaTopHeight)
            vsaTopDestRect = pg.Rect(0, tfa, width, vsaTopHeight)
            self._window.blit(buffer, vsaTopDestRect, vsaTopSrcRect)

            vsaBtmHeight = vsa - vsaTopHeight
            vsaBtmSrcRect = pg.Rect(0, tfa, width, vsaBtmHeight)
            vsaBtmDestRect = pg.Rect(0, tfa + vsaTopHeight, width, vsaBtmHeight)
            self._window.blit(buffer, vsaBtmDestRect, vsaBtmSrcRect)

            if bfa > 0:
                bfaRect = pg.Rect(0, tfa + vsa, width, bfa)
                self._window.blit(buffer, bfaRect, bfaRect)

    def show(self, param=None) -> None:
        """
        Show the display.
        """
        pg.display.flip()

    def deinit(self) -> None:
        """
        Deinitializes the pygame instance.
        """
        pg.display.quit()
        pg.quit()
