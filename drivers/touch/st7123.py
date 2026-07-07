# SPDX-License-Identifier: MIT
"""ST7123 TDDI capacitive touch (M5Stack Tab5 revision, I2C @ 0x55).

Port of Espressif ``esp_lcd_touch_st7123`` register layout for MicroPython polling.

Do **not** toggle a dedicated touch-reset GPIO on Tab5 — the ST7123 touch block is
gated by LCD reset. Hold ``irq_pin`` low (output) on Tab5; GPIO23 has a pull-up
that blocks touch otherwise (see M5Stack / esp-bsp ``bsp_touch_new``).
"""

from micropython import const

_DEFAULT_ADDR = const(0x55)
_REG_ADV_INFO = const(0x0010)
_REG_MAX_TOUCHES = const(0x0009)
_REG_REPORT_0 = const(0x0014)
_REPORT_SIZE = const(7)


class ST7123:
    def __init__(self, bus, *, address=_DEFAULT_ADDR, width=720, height=1280, irq_pin=None):
        self.bus = bus
        self.address = address
        self.width = width
        self.height = height
        self._irq_pin = irq_pin
        if irq_pin is not None:
            # Tab5: drive INT low so the on-board pull-up does not block touch.
            irq_pin.init(mode=irq_pin.OUT, pull=irq_pin.PULL_UP, value=0)

    def _read_reg(self, reg, size=1):
        return self.bus.readfrom_mem(self.address, reg, size, addrsize=16)

    def read_points(self):
        adv = self._read_reg(_REG_ADV_INFO)[0]
        if not (adv & 0x08):  # with_coord
            return 0, ()
        max_touches = self._read_reg(_REG_MAX_TOUCHES)[0]
        if max_touches == 0:
            return 0, ()
        nbytes = max_touches * _REPORT_SIZE
        raw = self._read_reg(_REG_REPORT_0, nbytes)
        points = []
        for i in range(max_touches):
            off = i * _REPORT_SIZE
            status = raw[off]
            if not (status & 0x80):  # valid (bit 7)
                continue
            x = (status & 0x3F) << 8 | raw[off + 1]
            y = raw[off + 2] << 8 | raw[off + 3]
            area = raw[off + 4]
            points.append((x, y, area, i))
        return len(points), tuple(points)
