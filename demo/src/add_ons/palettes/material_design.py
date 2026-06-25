# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`palettes.material_design`
====================================================
This module contains the Material Design color palette as a class object.


Usage:
    from palettes import get_palette
    palette = get_palette(name="material_design", color_depth=16, swapped=False)
    # OR
    palette = get_palette("material_design")

    # OR
    from palettes.material_design import MDPalette
    palette = MDPalette(size=5, color_depth=24)

    # to access the primary variant of a color family by name:
    x = palette.RED
    x = palette.BLACK

    # to access all 256 colors directly:
    x = palette[127]  # color at index 127

    # to access a shade by name:
    x = palette.RED_S500  # shade 500
    x = palette.RED_S900  # shade 900
    x = palette.RED_S50  # shade 50

    # to access an accent of a color family by name:
    x = palette.RED_A100
    x = palette.RED_A700

    # to iterate over all 256 colors:
        for x in palette:
            pass
"""

from . import MappedPalette
from ._material_design import COLORS, FAMILIES, LENGTHS


class MDPalette(MappedPalette):
    """
    A class to represent the Material Design color palette.
    """

    _shades = [
        "S50",
        "S100",
        "S200",
        "S300",
        "S400",
        "S500",
        "S600",
        "S700",
        "S800",
        "S900",
    ]

    _accents = ["A100", "A200", "A400", "A700"]

    def __init__(self, name="", color_depth=16, swapped=False, color_map=COLORS):
        super().__init__(name, color_depth, swapped, color_map)
        self._name = name if name else "MaterialDesign"

    def _define_named_colors(self):
        # The colors are already available as pal[0], pal[1], etc.
        # Now we want to add pal.BLACK = pal[0], pal.WHITE = pal[1], etc.
        color_index = 0
        for name, length in zip(FAMILIES, LENGTHS):
            if length == 1:  # black or white
                setattr(self, name.upper(), self[color_index])
                color_index += 1
            else:
                for shade in self._shades:
                    setattr(self, f"{name}_{shade}".upper(), self[color_index])
                    # S500 is the default shade for each family, so add it to the palette
                    # without the _S500 suffix
                    if shade == "S500":
                        setattr(self, name.upper(), self[color_index])
                    color_index += 1
                if length == 14:
                    for accent in self._accents:
                        setattr(self, f"{name}_{accent}".upper(), self[color_index])
                        color_index += 1
