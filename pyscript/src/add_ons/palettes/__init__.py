# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`palettes`
====================================================
"""

# The 16 colors of the standard Windows 16-color palette
WIN16 = {
    0x000000: "Black",
    0x000080: "Navy",
    0x0000FF: "Blue",
    0x008000: "Green",
    0x008080: "Teal",
    0x00FF00: "Lime",
    0x00FFFF: "Cyan",
    0x800000: "Maroon",
    0x800080: "Purple",
    0x808000: "Olive",
    0x808080: "Grey",
    0xC0C0C0: "Silver",
    0xFF0000: "Red",
    0xFF00FF: "Magenta",
    0xFFFF00: "Yellow",
    0xFFFFFF: "White",
}


def get_palette(name="default", **kwargs):
    if name == "wheel":
        from .wheel import WheelPalette as MyPalette
    elif name == "material_design":
        from .material_design import MDPalette as MyPalette
    elif name == "cube":
        from .cube import CubePalette as MyPalette
    else:
        MyPalette = Palette
    return MyPalette(name, **kwargs)


class Palette:
    """
    A class to represent a color palette.
    """

    def __init__(self, name="", color_depth=16, swapped=False, cached=False):
        self._name = name
        self._color_depth = color_depth
        self._swapped = swapped
        self._cache = {} if cached else None

        if not hasattr(self, "_names"):
            self._names = WIN16
        if not hasattr(self, "_length"):
            self._length = len(self._names)

        self._define_named_colors()

    def _define_named_colors(self):
        for color, name in self._names.items():
            if self._color_depth == 16:
                color = self.color565(color)
            elif self._color_depth == 8:
                color = self.color332(color)
            elif self._color_depth == 4:
                color = list(self._names.keys()).index(color)
            setattr(self, name.replace(" ", "_").upper(), color)

    @property
    def name(self):
        return self._name

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        index = self._normalize(index)

        if self._cache is not None and index in self._cache:
            return self._cache[index]

        r, g, b = self._get_rgb(index)
        if self._color_depth == 24 or self._color_depth == 4:
            return r << 16 | g << 8 | b
        elif self._color_depth == 16:
            return self.color565(r, g, b)
        elif self._color_depth == 8:
            return self.color332(r, g, b)
        raise ValueError("Invalid color depth")

    def _normalize(self, index):
        while index < 0:
            index += len(self)
        if index >= len(self):
            index %= len(self)
        return index

    def color565(self, r, g=None, b=None):
        if isinstance(r, (tuple, list)):
            # r is a tuple or list
            r, g, b = r
        elif g is None:
            # r is a 24-bit color
            r, g, b = r >> 16 & 0xFF, r >> 8 & 0xFF, r & 0xFF

        color = (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3
        if self._swapped:
            return (color & 0xFF) << 8 | (color & 0xFF00) >> 8
        else:
            return color

    def color332(self, r, g=None, b=None):
        # Convert r, g, b to 8-bit
        if isinstance(r, (tuple, list)):
            # r is a tuple or list
            r, g, b = r
        elif g is None:
            # r is a 24-bit color
            r, g, b = r >> 16 & 0xFF, r >> 8 & 0xFF, r & 0xFF

        color = (r & 0xE0) | (g & 0xE0) >> 3 | (b & 0xC0) >> 6
        return color

    def color_rgb(self, color):
        """
        color can be an 16-bit integer or a tuple, list or bytearray of length 2 or 3.
        """
        if isinstance(color, int):
            # convert 16-bit int color to 2 bytes
            color = (color & 0xFF, color >> 8)
        if len(color) == 2:
            r = color[1] & 0xF8 | (color[1] >> 5) & 0x7  # 5 bit to 8 bit red
            g = color[1] << 5 & 0xE0 | (color[0] >> 3) & 0x1F  # 6 bit to 8 bit green
            b = color[0] << 3 & 0xF8 | (color[0] >> 2) & 0x7  # 5 bit to 8 bit blue
        else:
            r, g, b = color
        return (r, g, b)

    def color_name(self, index):
        return self.rgb_name(self._get_rgb(self._normalize(index)))

    def rgb_name(self, r, g=None, b=None):
        if isinstance(r, (tuple, list)):
            r, g, b = r
        return self._names.get(r << 16 | g << 8 | b, f"#{r:02X}{g:02X}{b:02X}")

    def luminance(self, index):
        r, g, b = self._get_rgb(index)
        return 0.299 * r + 0.587 * g + 0.114 * b

    def brightness(self, index):
        r, g, b = self._get_rgb(index)
        return (r + g + b) / 3 / 255

    def _get_rgb(self, index):
        color = list(self._names.keys())[index]
        return color >> 16 & 0xFF, color >> 8 & 0xFF, color & 0xFF


class MappedPalette(Palette):
    """
    A class to represent a color palette with a color map.
    """

    def __init__(self, name, color_depth, swapped, color_map):
        self._color_map = color_map
        self._length = len(color_map) // 3
        super().__init__(name, color_depth, swapped)

    def _get_rgb(self, index):
        r, g, b = self._color_map[index * 3 : index * 3 + 3]
        return r, g, b
