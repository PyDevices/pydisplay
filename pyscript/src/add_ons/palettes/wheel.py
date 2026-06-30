"""
`pypalette.wheel`
====================================================
This module contains the cool wheel color palette as a class object.


Usage:
    from palettes import get_palette
    palette = get_palette(name="wheel", color_depth=16, swapped=False, length=256)
    # OR
    palette = get_palette(name="wheel")

    # OR
    from palettes.wheel import WheelPalette
    palette = WheelPalette(color_depth=16, swapped=False, length=256)

    print(f"Palette: {palette.name}, Length: {len(palette)}")
    for i, color in enumerate(palette):
        for i, color in enumerate(palette):  print(f"{i}. {color:#06X} {palette.color_name(i)}")

    # to access the named colors directly:
    x = palette.RED
    x = palette.BLACK

"""

from . import Palette as _Palette


class WheelPalette(_Palette):
    """
    A class to represent a color wheel as a palette.
    """

    def __init__(
        self,
        name="",
        color_depth=16,
        swapped=False,
        cached=True,
        length=256,
        saturation=1.0,
        value=None,
    ):
        self._length = length

        if saturation is None and value is None:
            self._mode = "wheel"
            self._one_third = self._length // 3
            self._two_thirds = 2 * self._length // 3
            self._spacing = 256 * 3 / self._length
        else:
            self._mode = "hsv"
            self._saturation = saturation if saturation is not None else 1.0
            self._value = value if value is not None else 1.0
            if not 0 <= self._saturation <= 1 or not 0 <= self._value <= 1:
                raise ValueError("Saturation and value must be in the range of 0-1")
        from . import WIN16 as NAMES

        self._names = NAMES

        super().__init__(name + str(self._length), color_depth, swapped, cached)

    def _get_rgb(self, index):
        if self._mode == "wheel":
            return self._wheel_to_rgb(index)
        else:
            return self._hsv_to_rgb(index / self._length, self._saturation, self._value)

    def _wheel_to_rgb(self, index):
        # incoming index is in the range of 0-self._length
        index = self._length - 1 - index  # reverse the order

        if index < self._one_third:
            return (255 - int(index * self._spacing), 0, int(index * self._spacing))
        elif index < self._two_thirds:
            index -= self._one_third
            return (0, int(index * self._spacing), 255 - int(index * self._spacing))
        else:
            index -= self._two_thirds
            return (int(index * self._spacing), 255 - int(index * self._spacing), 0)

    def _hsv_to_rgb(self, h, s, v):
        # incoming values are in the range of 0-1
        # returns r, g, b values in the range of 0-255
        if s == 0:  # when s=0, all values are shades of gray
            return int(v * 255), int(v * 255), int(v * 255)
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = int(255 * v * (1.0 - s))
        q = int(255 * v * (1.0 - s * f))
        t = int(255 * v * (1.0 - s * (1.0 - f)))
        v = int(255 * v)
        i = i % 6
        if i == 0:  # red
            return v, t, p
        if i == 1:  # yellow
            return q, v, p
        if i == 2:  # green
            return p, v, t
        if i == 3:  # cyan
            return p, q, v
        if i == 4:  # blue
            return t, p, v
        if i == 5:  # magenta
            return v, p, q
        return 0, 0, 0
