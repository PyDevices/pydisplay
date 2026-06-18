"""
Adapted from:
    https://github.com/lewisxhe/SensorLib/blob/master/src/touch/TouchClassCST226.cpp
"""

from time import sleep_ms

from machine import Pin
from micropython import const

# CST226-specific constants
_CST226_ID = const(0xA8)  # CST226 specific chip ID
_CST226_REG_STATUS = const(0x00)
_CST226_BUFFER_NUM = const(28)

# Register Definitions
_REG_SLEEP_MODE = const(0xE5)
_REG_LONG_PRESS_TICK = const(0xEB)
_REG_MOTION_MASK = const(0xEC)
_REG_IRQ_CTL = const(0xFA)
_REG_DIS_AUTOSLEEP = const(0xFE)

# Motion and IRQ masks
MOTION_MASK_CONTINUOUS_LEFT_RIGHT = const(0b100)
MOTION_MASK_CONTINUOUS_UP_DOWN = const(0b010)
MOTION_MASK_DOUBLE_CLICK = const(0b001)

IRQ_EN_TOUCH = const(0x40)
IRQ_EN_CHANGE = const(0x20)
IRQ_EN_MOTION = const(0x10)
IRQ_EN_LONGPRESS = const(0x01)


class CST226:
    def __init__(
        self,
        bus,
        address=0x5A,
        rst_pin=None,
        irq_pin=None,
        irq_handler=lambda pin: None,
        irq_en=0x00,
        motion_mask=0b000,
    ):
        self._bus = bus
        self._address = address

        # Detect if the chip is CST226
        buffer = bytearray(8)
        write_buffer = bytearray(2)
        write_buffer[0] = 0xD2
        write_buffer[1] = 0x04
        self._write_then_read(write_buffer, buffer, 4)
        chipType = (buffer[3] << 8) | buffer[2]
        if chipType != _CST226_ID:
            raise ValueError("Error: CST226 not detected.")

        # Setup pins and reset the device
        self.rst = Pin(rst_pin, Pin.OUT) if isinstance(rst_pin, int) else rst_pin
        self.reset()
        self.disable_autosleep()

        # Setup interrupt pin if available
        self.irq = Pin(irq_pin, Pin.IN, Pin.PULL_UP) if isinstance(irq_pin, int) else irq_pin
        if self.irq:
            self.irq.irq(trigger=Pin.IRQ_FALLING, handler=irq_handler)
            self.set_irq_ctl(irq_en, motion_mask)

    def touched(self):
        # Read finger count for the CST226
        return self._read(0x02)[0]

    def get_point(self):
        # CST226-specific point handling
        buffer = self._read(_CST226_REG_STATUS, _CST226_BUFFER_NUM)
        if buffer[0] == 0xAB or buffer[5] == 0x80:
            return 0  # No touch detected or button press

        point_count = buffer[5] & 0x7F
        if point_count > 5 or point_count == 0:
            self._write(0x00, 0xAB)
            return 0

        points = []
        index = 0
        for i in range(point_count):
            x = (buffer[index + 1] << 4) | ((buffer[index + 3] >> 4) & 0x0F)
            y = (buffer[index + 2] << 4) | (buffer[index + 3] & 0x0F)
            points.append((x, y))
            index += 7 if i == 0 else 5

        return points

    def get_gestures(self):
        # CST226-specific gesture handling (not available in this example)
        return None

    def get_points(self):
        raise NotImplementedError("get_points() not implemented (yet)")

    def reset(self):
        if self.rst:
            self.rst(0)
            sleep_ms(1)
            self.rst(1)
            sleep_ms(50)
        else:
            # For CST226 specific reset
            self._write(0xD1, 0x0E)
            sleep_ms(20)

    def disable_autosleep(self, val=0x01):
        self._write(_REG_DIS_AUTOSLEEP, val)

    def set_irq_ctl(self, irq_en, motion_mask=0b000):
        self._write(_REG_IRQ_CTL, irq_en)
        self._write(_REG_MOTION_MASK, motion_mask)

    def set_long_press_tick(self, val):
        self._write(_REG_LONG_PRESS_TICK, val)

    def set_sleep_mode(self, val):
        self._write(_REG_SLEEP_MODE, val)

    def sleep(self):
        # CST226-specific sleep command
        self._write(0xD1, 0x05)

    def wakeup(self):
        # CST226-specific wakeup using reset
        self.reset()

    def get_resolution(self):
        # CST226-specific resolution handling
        buffer = self._read(0xD1, 8)
        x_res = (buffer[1] << 8) | buffer[0]
        y_res = (buffer[3] << 8) | buffer[2]
        return x_res, y_res

    def _read(self, reg, length=1):
        return self._bus.readfrom_mem(self._address, int(reg), length)

    def _write(self, reg, val):
        self._bus.writeto_mem(self._address, int(reg), bytes([int(val)]))

    def _write_then_read(self, write_buffer, read_buffer, read_length):
        self._bus.writeto(self._address, write_buffer)
        read_data = self._bus.readfrom(self._address, read_length)
        for i in range(read_length):
            read_buffer[i] = read_data[i]
