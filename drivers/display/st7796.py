"""
The init sequence is written out line by line in .init()
"""

try:
    from displaysys.busdisplay import BusDisplay
except ImportError:
    from busdisplay import BusDisplay
from time import sleep_ms

from micropython import const

_SWRESET = const(0x01)
_SLPOUT = const(0x11)
_CSCON = const(0xF0)
_MADCTL = const(0x36)
_COLMOD = const(0x3A)
_DIC = const(0xB4)
_DFC = const(0xB6)
_DOCA = const(0xE8)
_PWR2 = const(0xC1)
_PWR3 = const(0xC2)
_VCMPCTL = const(0xC5)
_PGC = const(0xE0)
_NGC = const(0xE1)
_DISPON = const(0x29)


class ST7796(BusDisplay):
    """ST7796 display driver"""

    def __init__(self, bus, **kwargs):
        super().__init__(bus, **kwargs)

    def init(self):
        #         self.rotation_table = _ROTATION_TABLE
        param_buf = bytearray(14)
        param_mv = memoryview(param_buf)

        self.send(_SWRESET)

        sleep_ms(120)

        self.send(_SLPOUT)

        sleep_ms(120)

        param_buf[0] = 0xC3
        self.send(_CSCON, param_mv[:1])

        param_buf[0] = 0x96
        self.send(_CSCON, param_mv[:1])

        if self.color_depth // 8 == 2:
            pixel_format = 0x55
        elif self.color_depth // 8 == 3:
            pixel_format = 0x77
        else:
            raise RuntimeError(
                "ST7796 IC only supports lv.COLOR_FORMAT.RGB565 or lv.COLOR_FORMAT.RGB888"
            )

        param_buf[0] = pixel_format
        self.send(_COLMOD, param_mv[:1])

        param_buf[0] = 0x01
        self.send(_DIC, param_mv[:1])

        param_buf[0] = 0x80
        param_buf[1] = 0x02
        param_buf[2] = 0x3B
        self.send(_DFC, param_mv[:3])

        param_buf[:8] = bytearray([0x40, 0x8A, 0x00, 0x00, 0x29, 0x19, 0xA5, 0x33])
        self.send(_DOCA, param_mv[:8])

        param_buf[0] = 0x06
        self.send(_PWR2, param_mv[:1])

        param_buf[0] = 0xA7
        self.send(_PWR3, param_mv[:1])

        param_buf[0] = 0x18
        self.send(_VCMPCTL, param_mv[:1])

        sleep_ms(120)

        param_buf[:14] = bytearray(
            [
                0xF0,
                0x09,
                0x0B,
                0x06,
                0x04,
                0x15,
                0x2F,
                0x54,
                0x42,
                0x3C,
                0x17,
                0x14,
                0x18,
                0x1B,
            ]
        )
        self.send(_PGC, param_mv[:14])

        param_buf[:14] = bytearray(
            [
                0xE0,
                0x09,
                0x0B,
                0x06,
                0x04,
                0x03,
                0x2B,
                0x43,
                0x42,
                0x3B,
                0x16,
                0x14,
                0x17,
                0x1B,
            ]
        )
        self.send(_NGC, param_mv[:14])

        sleep_ms(120)

        param_buf[0] = 0x3C
        self.send(_CSCON, param_mv[:1])

        param_buf[0] = 0x69
        self.send(_CSCON, param_mv[:1])

        sleep_ms(120)

        self.send(_DISPON)

        sleep_ms(120)

        super().init()
