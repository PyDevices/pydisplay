"""XPT2046 Touch module Micropython driver.

Made by Lesept (May 2023)
Inspired by https://github.com/rdagger/micropython-ili9341

"""

from time import sleep

from micropython import const


class Touch(object):
    """Serial interface for XPT2046 Touch Screen Controller."""

    GET_X = const(0b11010000)  # X position
    GET_Y = const(0b10010000)  # Y position

    def __init__(self, spi, cs, int_pin=None, int_handler=None):
        self.spi = spi
        self.cs = cs
        self.cs.init(self.cs.OUT, value=1)
        self.cal = False
        self.rx_buf = bytearray(3)  # Receive buffer
        self.tx_buf = bytearray(3)  # Transmit buffer
        if int_pin is not None:
            self.int_pin = int_pin
            self.int_pin.init(int_pin.IN)
        if int_handler is not None:
            self.int_handler = int_handler
            self.int_locked = False
            int_pin.irq(trigger=int_pin.IRQ_FALLING | int_pin.IRQ_RISING, handler=self.int_press)

    def set_orientation(self, orientation):
        self.orientation = orientation

    def int_press(self, pin):
        """Send X,Y values to passed interrupt handler."""
        if not pin.value() and not self.int_locked:
            self.int_locked = True  # Lock Interrupt
            x, y = self.get_touch()
            self.int_handler(x, y)
            sleep(0.1)  # Debounce falling edge
        elif pin.value() and self.int_locked:
            sleep(0.1)  # Debounce rising edge
            self.int_locked = False  # Unlock interrupt

    def calibrate(self, xmin, xmax, ymin, ymax, width, height, orientation):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.orientation = orientation
        if self.orientation % 2 == 0:
            self.width = height
            self.height = width
        else:
            self.width = width
            self.height = height
        self.cal = True

    def raw_touch(self):
        x = self.send_command(self.GET_X)
        y = self.send_command(self.GET_Y)
        return x, y

    def map_value(self, v, vmin, vmax, maxv):
        # Map x or y value to display
        return int((v - vmin) / (vmax - vmin) * maxv)

    def get_touch(self, clip=False):
        if not self.cal:
            print("Touch is not calibrated: use raw_touch or calibrate")
            return 0, 0
        xraw, yraw = self.raw_touch()
        x = self.map_value(xraw, self.xmin, self.xmax, self.width)
        y = self.map_value(yraw, self.ymin, self.ymax, self.height)

        # Clip values
        if clip:
            x = max(x, 0)
            y = max(y, 0)
            x = min(x, self.width)
            y = min(y, self.height)

        if self.orientation % 2 == 1:
            return y, self.width - x
        else:
            return x, y

    def is_touched(self):
        return self.int_pin.value() == 0

    def send_command(self, command):
        # Write command to XPT2046
        self.tx_buf[0] = command
        self.cs(0)
        self.spi.write_readinto(self.tx_buf, self.rx_buf)
        self.cs(1)
        return (self.rx_buf[1] << 4) | (self.rx_buf[2] >> 4)
