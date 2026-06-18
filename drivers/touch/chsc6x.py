# SPDX-FileCopyrightText: 2023 Brad Barnett
#
# SPDX-License-Identifier: MIT
#
# Suggest setting I2C freq = 400000 and using IRQ pin for best performance
# Set IRQ speed to 100000 if not using an IRQ pin


from time import sleep_ms

from machine import I2C, Pin
from micropython import const

CHSC6X_I2C_ID = const(0x2E)
CHSC6X_READ_POINT_LEN = const(5)


class CHSC6X:
    def __init__(self, i2c, addr=CHSC6X_I2C_ID, irq_pin=None):
        self._i2c = i2c
        self._addr = addr
        self._irq = Pin(irq_pin, Pin.IN, Pin.PULL_UP) if irq_pin else None
        self._buffer = bytearray(CHSC6X_READ_POINT_LEN)
        sleep_ms(100)

    def is_touched(self):
        if self._irq is not None:
            return self._irq.value() is False
        return self.touch_read() is not None

    def touch_read(self):
        if self._irq is not None:
            if self.is_touched() is True:
                self._i2c.readfrom_into(self._addr, self._buffer)
            else:
                return None
        else:
            try:
                self._i2c.readfrom_into(self._addr, self._buffer)
            except OSError:  # Thrown when reading too fast
                return None

        results = list(self._buffer)
        # first byte is non-zero when touched, 3rd byte is x, 5th byte is y
        if results[0]:
            return results[2], results[4]
        return None


def main():
    print("Started...")
    i2c = I2C(0, sda=Pin(7), scl=Pin(6), freq=400000)
    touch = CHSC6X(i2c, irq_pin=16)

    while True:
        if touch.is_touched():
            print("Touched: ", touch.touch_read())


if __name__ == "__main__":
    main()
