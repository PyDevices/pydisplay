# SPDX-FileCopyrightText: 2024 Brad Barnett and Kevin Schlosser
#
# SPDX-License-Identifier: MIT

"""
displaysys.busdisplay
"""

import gc
import struct
import sys

from micropython import const

from displaysys import DisplayDriver

if sys.implementation.name == "micropython":
    from time import sleep_ms

    from machine import Pin
    from micropython import alloc_emergency_exception_buf

    alloc_emergency_exception_buf(256)
elif sys.implementation.name == "circuitpython":
    from time import sleep

    import digitalio

    def sleep_ms(ms):
        return sleep(ms / 1000)
else:
    raise ImportError("BusDisplay is not supported on this platform.")


# MIPI DCS (Display Command Set) Command Constants
_INVOFF = const(0x20)
_INVON = const(0x21)
_CASET = const(0x2A)
_RASET = const(0x2B)
_RAMWR = const(0x2C)
_COLMOD = const(0x3A)
_MADCTL = const(0x36)
_RAMCONT = const(0x3C)
_SWRESET = const(0x01)
_SLPIN = const(0x10)
_SLPOUT = const(0x11)
_VSCRDEF = const(0x33)
_VSCSAD = const(0x37)

# fmt: off

# MIPI DCS MADCTL bits
# Bits 0 (Flip Vertical) and 1 (Flip Horizontal) affect how the display is refreshed, not how frame memory is written.
# Instead of using them, we only change Bits 6 (column/horizontal) and 7 (page/vertical).
_RGB = const(0x00)  # (Bit 3: 0=RGB order, 1=BGR order)
_BGR = const(0x08)  # (Bit 3: 0=RGB order, 1=BGR order)
_MADCTL_MV = const(0x20)  # 0=Normal, 1=Row/column exchange (Bit 5: Page/Column Addressing Order)
_MADCTL_MX = const(0x40)  # 0=Left to Right, 1=Right to Left (Bit 6: Column Address Order)
_MADCTL_MY = const(0x80)  # 0=Top to Bottom, 1=Bottom to Top (Bit 7: Page Address Order)

# MADCTL values for each of the rotation constants.
_DEFAULT_ROTATION_TABLE = (
    _MADCTL_MX,  # mirrored = False, rotation = 0
    _MADCTL_MV,  # mirrored = False, rotation = 90
    _MADCTL_MY,  # mirrored = False, rotation = 180
    _MADCTL_MY | _MADCTL_MX | _MADCTL_MV,  # mirrored = False, rotation = 270
)

_MIRRORED_ROTATION_TABLE = (
    0,  # mirrored = True, rotation = 0
    _MADCTL_MV | _MADCTL_MX,  # mirrored = True, rotation = 90
    _MADCTL_MX | _MADCTL_MY,  # mirrored = True, rotation = 180
    _MADCTL_MV | _MADCTL_MY,  # mirrored = True, rotation = 270
)
# fmt: on


class BusDisplay(DisplayDriver):
    """
    Base class for displays connected via a bus.

    Args:
        display_bus (SPIBus, I80Bus): The bus the display is connected to.
        init_sequence (bytes, list): The initialization sequence for the display.
        width (int): The width of the display in pixels.
        height (int): The height of the display in pixels.
        colstart (int): The column start address for the display.
        rowstart (int): The row start address for the display.
        rotation (int): The rotation of the display in degrees.
        mirrored (bool): If True, the display is mirrored.
        color_depth (int): The color depth of the display in bits.
        bgr (bool): If True, the display uses BGR color order.
        invert (bool): If True, the display colors are inverted.
        reverse_bytes_in_word (bool): If True, the bytes in 16-bit colors are reversed.
        brightness (float): The brightness of the display as a float between 0.0 and 1.0.
        backlight_pin (int, Pin): The pin the display backlight is connected to.
        backlight_on_high (bool): If True, the backlight is on when the pin is high.
        reset_pin (int, Pin): The pin the display reset is connected to.
        reset_high (bool): If True, the reset pin is high.
        power_pin (int, Pin): The pin the display power is connected to.
        power_on_high (bool): If True, the power pin is high.
        set_column_command (int): The command to set the column address.
        set_row_command (int): The command to set the row address.
        write_ram_command (int): The command to write to the display RAM.
        brightness_command (int): The command to set the display brightness.
        data_as_commands (bool): If True, data is sent as commands.
        single_byte_bounds (bool): If True, single byte bounds are used.

    Attributes:
        display_bus (SPIBus, I80Bus): The bus the display is connected to.
        color_depth (int): The color depth of the display in bits.
        bgr (bool): If True, the display uses BGR color order.
        rotation_table (tuple): The rotation table for the display.
    """

    def __init__(  # noqa: PLR0913
        self,
        display_bus,
        init_sequence=None,
        *,
        width=0,
        height=0,
        colstart=0,
        rowstart=0,
        rotation=0,
        mirrored=False,
        color_depth=16,
        bgr=False,
        invert=False,
        reverse_bytes_in_word=False,
        brightness=1.0,
        backlight_pin=None,
        backlight_on_high=True,
        reset_pin=None,
        reset_high=True,
        power_pin=None,
        power_on_high=True,
        set_column_command=_CASET,
        set_row_command=_RASET,
        write_ram_command=_RAMWR,
        brightness_command=None,  # For color OLEDs
        data_as_commands=False,  # For color OLEDs
        single_byte_bounds=False,  # For color OLEDs
    ):
        gc.collect()
        self.display_bus = display_bus
        self._width = width
        self._height = height
        self._colstart = colstart
        self._rowstart = rowstart
        self._rotation = rotation
        self.color_depth = color_depth
        self.bgr = bgr
        self._invert = invert
        self._requires_byteswap = reverse_bytes_in_word
        self._set_column_command = set_column_command
        self._set_row_command = set_row_command
        self._write_ram_command = write_ram_command
        self._brightness_command = brightness_command
        self._data_as_commands = data_as_commands  # not implemented
        self._single_byte_bounds = single_byte_bounds  # not implemented

        self.send = display_bus.send
        self.send_color = (
            display_bus.send if not hasattr(display_bus, "send_color") else display_bus.send_color
        )

        self.rotation_table = _DEFAULT_ROTATION_TABLE if not mirrored else _MIRRORED_ROTATION_TABLE

        self._param_buf = bytearray(4)
        self._param_mv = memoryview(self._param_buf)

        self._reset_pin = self._config_output_pin(reset_pin, value=not reset_high)
        self._reset_high = reset_high

        self._power_pin = self._config_output_pin(power_pin, value=power_on_high)
        self._power_on_high = power_on_high

        self._backlight_pin = self._config_output_pin(backlight_pin, value=backlight_on_high)
        self._backlight_on_high = backlight_on_high

        if self._backlight_pin is not None:
            try:
                from machine import PWM

                self._backlight_pin = PWM(self._backlight_pin, freq=1000, duty_u16=0)
                self._backlight_is_pwm = True
            except ImportError:
                # PWM not implemented on this platform or Pin
                self._backlight_is_pwm = False

        # Run the display driver init_sequence.
        if isinstance(init_sequence, bytes):
            self._init_bytes(init_sequence)
        elif isinstance(init_sequence, list) or isinstance(init_sequence, tuple):
            self._init_list(init_sequence)

        # Run the display driver init() method, which also gets called by rotation.setter
        # This should run immediately after _init_bytes() or _init_list() but before
        # sending other commands such as _INVON, _INVOFF, _COLMOD, brightness, etc.
        self._initialized = False
        super().__init__(auto_refresh=False)
        if not self._initialized:
            raise RuntimeError("Display driver init() must call super().init()")

        # Set COLMOD (color mode) based on color_depth
        pixel_formats = {3: 0x11, 8: 0x22, 12: 0x33, 16: 0x55, 18: 0x66, 24: 0x77}
        self._param_buf[0] = pixel_formats[self.color_depth]
        self.send(_COLMOD, self._param_mv[:1])

        self.brightness = brightness

        gc.collect()

    ############### Required API Methods ################

    def init(self) -> None:
        """
        Post initialization tasks.

        This method may be overridden by subclasses to perform any post initialization.
        If it is overridden, it must call super().init() or set self._initialized = True.
        """
        self._initialized = True

        # Convert from degrees to one quarter rotations.  Wrap at the number of entries in the rotations table.
        # For example, rotation = 90 -> index = 1.  With 4 entries in the rotation table, rotation = 540 -> index = 2
        index = (self._rotation // 90) % len(self.rotation_table)

        # Set the display MADCTL bits for the given rotation.
        self._param_buf[0] = self.rotation_table[index] | _BGR if self.bgr else _RGB
        self.send(_MADCTL, self._param_mv[:1])

        # Set the display inversion mode
        self.invert_colors(self._invert)

    def blit_rect(self, buf: memoryview, x: int, y: int, w: int, h: int):
        """
        Blit a buffer to the display.

        This method takes a buffer of pixel data and writes it to a specified
        rectangular area of the display. The top-left corner of the rectangle is
        specified by the x and y parameters, and the size of the rectangle is
        specified by the width and height parameters.

        Args:
            buf (memoryview): The buffer containing the pixel data.
            x (int): The x-coordinate of the top-left corner of the rectangle.
            y (int): The y-coordinate of the top-left corner of the rectangle.
            w (int): The width of the rectangle in pixels.
            h (int): The height of the rectangle in pixels.

        Returns:
            (tuple): A tuple containing the x, y, width, and height of the rectangle.
        """
        if self._auto_byteswap:
            self.byteswap(buf)

        x1 = x + self.colstart
        x2 = x1 + w - 1
        y1 = y + self.rowstart
        y2 = y1 + h - 1

        self._set_window(x1, y1, x2, y2)
        self.send_color(self._write_ram_command, buf)
        return (x, y, w, h)

    def fill_rect(self, x: int, y: int, w: int, h: int, c: int):
        """
        Draw a rectangle at the given location, size and filled with color.

        This method draws a filled rectangle on the display. The top-left corner of
        the rectangle is specified by the x and y parameters, and the size of the
        rectangle is specified by the width and height parameters. The rectangle is
        filled with the specified color.

        Args:
            x (int): The x-coordinate of the top-left corner of the rectangle.
            y (int): The y-coordinate of the top-left corner of the rectangle.
            w (int): The width of the rectangle in pixels.
            h (int): The height of the rectangle in pixels.
            c (int): The color of the rectangle.

        Returns:
            (tuple): A tuple containing the x, y, width, and height of the rectangle.
        """
        color_bytes = (
            (c & 0xFFFF).to_bytes(2, "big")
            if self._auto_byteswap
            else (c & 0xFFFF).to_bytes(2, "little")
        )
        x1 = x + self.colstart
        x2 = x1 + w - 1
        y1 = y + self.rowstart
        y2 = y1 + h - 1

        if h > w:
            buf = memoryview(bytearray(color_bytes * h))
            passes = w
        else:
            buf = memoryview(bytearray(color_bytes * w))
            passes = h

        self._set_window(x1, y1, x2, y2)
        self.send(_RAMWR)
        for _ in range(passes):
            self.send_color(_RAMCONT, buf)
        return (x, y, w, h)

    def pixel(self, x: int, y: int, c: int):
        """
        Set a pixel on the display.

        Args:
            x (int): The x-coordinate of the pixel.
            y (int): The y-coordinate of the pixel.
            c (int): The color of the pixel.

        Returns:
            (tuple): A tuple containing the x, y, width, and height of the pixel.
        """
        color_bytes = (
            (c & 0xFFFF).to_bytes(2, "big")
            if self._auto_byteswap
            else (c & 0xFFFF).to_bytes(2, "little")
        )
        xpos = x + self.colstart
        ypos = y + self.rowstart
        self._set_window(xpos, ypos, xpos, ypos)
        self.send(_RAMWR, color_bytes)
        return (x, y, 1, 1)

    ############### API Method Overrides ################

    def vscrdef(self, tfa: int, vsa: int, bfa: int) -> None:
        """
        Set Vertical Scrolling Definition.

        To scroll a 135x240 display these values should be 40, 240, 40.
        There are 40 lines above the display that are not shown followed by
        240 lines that are shown followed by 40 more lines that are not shown.
        You could write to these areas off display and scroll them into view by
        changing the TFA, VSA and BFA values.

        Args:
            tfa (int): Top Fixed Area.
            vsa (int): Vertical Scrolling Area.
            bfa (int): Bottom Fixed Area.
        """
        super().vscrdef(tfa, vsa, bfa)
        self.send(_VSCRDEF, struct.pack(">HHH", tfa, vsa, bfa))

    def vscsad(self, vssa=None) -> int:
        """
        Set the vertical scroll start address.

        Args:
            vssa (int, None): The vertical scroll start address.

        Returns:
            int: The vertical scroll start address.
        """
        if vssa is not None:
            super().vscsad(vssa)
            self.send(_VSCSAD, struct.pack(">H", self._vssa))
        return self._vssa

    ############### Optional API Methods ################

    @property
    def colstart(self):
        """
        The offset in pixels to the first column of the visible display.
        """
        rot = self.rotation % 360
        if rot == 0 or rot == 180:
            return self._colstart
        return self._rowstart

    @property
    def rowstart(self):
        """
        The offset in pixels to the first row of the visible display.
        """
        rot = self.rotation % 360
        if rot == 0 or rot == 180:
            return self._rowstart
        return self._colstart

    @property
    def power(self) -> bool:
        """
        The power state of the display.

        Returns:
            bool: The power state of the display.
        """
        if self._power_pin is None:
            return -1

        state = self._power_pin.value()
        if self._power_on_high:
            return state

        return not state

    @power.setter
    def power(self, value: bool) -> None:
        """
        Set the power state of the display.

        Args:
            value (bool): The power state to set, True for on, False for off.
        """
        if self._power_pin is None:
            return

        if self._power_on_high:
            self._power_pin.value(value)
        else:
            self._power_pin.value(not value)

    @property
    def brightness(self) -> float:
        """
        The brightness of the display.
        """
        if self._backlight_pin is None and self._brightness_command is None:
            return -1

        return self._brightness

    @brightness.setter
    def brightness(self, value: float) -> None:
        """
        Set the brightness of the display.

        Args:
            value (float): The brightness of the display as a float between 0.0 and 1.0.
        """
        if 0 <= float(value) <= 1:
            self._brightness = value
            if self._backlight_pin:
                if not self._backlight_on_high:
                    value = 1 - value
                if self._backlight_is_pwm:
                    if sys.implementation.name == "micropython":
                        self._backlight_pin.duty_u16(int(value * 0xFFFF))
                    elif sys.implementation.name == "circuitpython":
                        self._backlight_pin.duty_cycle = int(value * 0xFFFF)
                else:
                    if sys.implementation.name == "micropython":
                        self._backlight_pin.value(value > 0.5)  # noqa: PLR2004
                    elif sys.implementation.name == "circuitpython":
                        self._backlight_pin.value = value > 0.5  # noqa: PLR2004
            elif self._brightness_command is not None:
                self._param_buf[0] = int(value * 255)
                self.send(self._brightness_command, self._param_mv[:1])

    def invert_colors(self, value: bool) -> None:
        """
        Invert the colors of the display.

        Args:
            value (bool): If True, invert the colors of the display.
        """
        if value:
            self.send(_INVON)
        else:
            self.send(_INVOFF)

    def reset(self) -> None:
        """
        Reset display.

        This method resets the display. If the display has a reset pin, it is
        reset using the reset pin. Otherwise, the display is reset using the
        software reset command.
        """
        if self._reset_pin is not None:
            self.hard_reset()
        else:
            self.soft_reset()

    def hard_reset(self) -> None:
        """
        Hard reset display.
        """
        self._reset_pin.value(self._reset_high)
        sleep_ms(120)
        self._reset_pin.value(not self._reset_high)

    def soft_reset(self) -> None:
        """
        Soft reset display.
        """
        self.send(_SWRESET)
        sleep_ms(150)

    def sleep_mode(self, value: bool) -> None:
        """
        Enable or disable display sleep mode.

        Args:
            value (bool): If True, enable sleep mode. If False, disable sleep mode.
        """
        self.send(_SLPIN if value else _SLPOUT)

    def _deinit(self) -> None:
        """Best-effort hardware teardown."""
        try:
            self.brightness = 0
        except Exception:
            pass
        try:
            self.power = False
        except Exception:
            pass
        bus = getattr(self, "display_bus", None)
        if bus is not None and hasattr(bus, "deinit"):
            bus.deinit()
        self.display_bus = None
        for attr in ("_backlight_pin", "_reset_pin", "_power_pin"):
            pin = getattr(self, attr, None)
            if pin is not None and hasattr(pin, "deinit"):
                try:
                    pin.deinit()
                except Exception:
                    pass
            setattr(self, attr, None)

    ############### Class Specific Methods ##############

    def _set_window(self, x1, y1, x2, y2):
        # See https://github.com/adafruit/Adafruit_Blinka_Displayio/blob/main/displayio/_displaysys.py#L271-L363
        # TODO:  Add `if self._single_byte_bounds is True:` for Column and Row _param_buf packing

        # Column addresses
        self._param_buf[0] = (x1 >> 8) & 0xFF
        self._param_buf[1] = x1 & 0xFF
        self._param_buf[2] = (x2 >> 8) & 0xFF
        self._param_buf[3] = x2 & 0xFF
        self.send(self._set_column_command, self._param_mv[:4])

        # Row addresses
        self._param_buf[0] = (y1 >> 8) & 0xFF
        self._param_buf[1] = y1 & 0xFF
        self._param_buf[2] = (y2 >> 8) & 0xFF
        self._param_buf[3] = y2 & 0xFF
        self.send(self._set_row_command, self._param_mv[:4])

    def _init_bytes(self, init_sequence):
        """
        Send an initialization sequence to the display.

        Used by display driver subclass if init_sequence is a CircuitPython displayIO compatible bytes object.
        The ``init_sequence`` is bitpacked to minimize the ram impact. Every command begins
        with a command byte followed by a byte to determine the parameter count and if a
        delay is need after. When the top bit of the second byte is 1, the next byte will be
        the delay time in milliseconds. The remaining 7 bits are the parameter count
        excluding any delay byte. The third through final bytes are the remaining command
        parameters. The next byte will begin a new command definition.

        Args:
            init_sequence (bytes): The initialization sequence to send to the display.
        """
        DELAY = 0x80

        i = 0
        while i < len(init_sequence):
            command = init_sequence[i]
            data_size = init_sequence[i + 1]
            delay = (data_size & DELAY) != 0
            data_size &= ~DELAY

            self.send(command, init_sequence[i + 2 : i + 2 + data_size])

            delay_time_ms = 10
            if delay:
                data_size += 1
                delay_time_ms = init_sequence[i + 1 + data_size]
                if delay_time_ms == 255:
                    delay_time_ms = 500

            sleep_ms(delay_time_ms)
            i += 2 + data_size

    def _init_list(self, init_sequence):
        """
        Send an initialization sequence to the display.

        Used by display driver subclass if init_sequence is a list of tuples.
        As a list, it can be modified in .init(), for example:
            self._INIT_SEQUENCE[-1] = (0x29, b"\x00", 100)
        Each tuple contains the following:
            - The first element is the register address (command)
            - The second element is the register value (data)
            - The third element is the delay in milliseconds after the register is set

        Args:
            init_sequence (list): The initialization sequence to send to the display
        """
        for line in init_sequence:
            self.send(line[0], line[1])
            if line[2] != 0:
                sleep_ms(line[2])

    def _config_output_pin(self, pin, value=None):
        if pin is None:
            return None

        if sys.implementation.name == "micropython":
            p = Pin(pin, Pin.OUT)
            if value is not None:
                p.value(value)
        elif sys.implementation.name == "circuitpython":
            p = digitalio.DigitalInOut(pin)
            p.direction = digitalio.Direction.OUTPUT
            if value is not None:
                p.value = value
        return p
