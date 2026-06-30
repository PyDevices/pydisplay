# SPDIX:# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`palettes.cube`
====================================================
Makes a color cube palette.

Usage:
    from palettes import get_palette
    palette = get_palette(name="cube", size=5, color_depth=16, swapped=False)
    # OR
    palette = get_palette(name="cube")

    # OR
    from palettes.cube import CubePalette
    palette = CubePalette(size=5, color_depth=24)

    print(f"Palette: {palette.name}, Length: {len(palette)}")
    for i, color in enumerate(palette):
        for i, color in enumerate(palette):  print(f"{i}. {color:#06X} {palette.color_name(i)}")
"""

from . import Palette as _Palette


class CubePalette(_Palette):
    """
    A color cube palette.  The size of the cube is determined by the size parameter.
    """

    def __init__(self, name="", color_depth=16, swapped=False, cached=True, size=5):
        self._size = size
        self._length = size**3
        self._values = [round(i * (255 / (size - 1)) + 0.25) for i in range(size)]

        if self._size == 2:
            from ._cube8 import CUBE8 as NAMES
        elif self._size == 3:
            from ._cube27 import CUBE27 as NAMES
        elif self._size == 4:
            from ._cube64 import CUBE64 as NAMES
        else:
            from ._cube125 import CUBE125 as NAMES
        self._names = NAMES
        super().__init__(name + str(self._length), color_depth, swapped, cached)

    def _get_rgb(self, index):
        z = index % self._size
        index //= self._size
        y = index % self._size
        index //= self._size
        x = index % self._size
        return self._values[x], self._values[y], self._values[z]
