# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT


def get_palette(sender=None, name="material_design", color_depth=16, swapped=False, **kwargs):
    if name == "wheel":
        from .wheel import Palette
    elif name == "material_design":
        from .material_design import Palette
    else:
        from ._palette import Palette
    return Palette(name, color_depth, swapped, **kwargs)