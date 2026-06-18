# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Constants used by the pdwidgets library.
"""

from micropython import const

PAD = const(2)
DEFAULT_PADDING = (PAD, PAD, PAD, PAD)
TEXT_WIDTH = const(8)


class _Constants:
    """
    A base class for creating a struct-like class.  The class may be used to check if a value is one of the built-in values, for instance:
    ```
    CONSTANTS = _Constants()
    if value in CONSTANTS:
        print("Value is valid")
    ```
    May also be used to iterate over the values:
    ```
    CONSTANTS = _Constants()
    for value in CONSTANTS:
        print(value)
    ```
    """

    @classmethod
    def __contains__(cls, item):
        return item in cls.__dict__.values()

    @classmethod
    def __iter__(cls):
        return iter(cls.__dict__.values())


class _IconSize(_Constants):
    SMALL = 18
    MEDIUM = 24
    LARGE = 36
    XLARGE = 48


ICON_SIZE = _IconSize()


class _TextSize(_Constants):
    SMALL = 8
    MEDIUM = 14
    LARGE = 16


TEXT_SIZE = _TextSize()


class _Position(_Constants):
    LEFT = 1 << 0
    RIGHT = 1 << 1
    TOP = 1 << 2
    BOTTOM = 1 << 3
    OUTER = 1 << 4


POSITION = _Position()


class _Align(_Constants):
    CENTER = 0  # 0
    TOP_LEFT = POSITION.TOP | POSITION.LEFT  # 5
    TOP = POSITION.TOP  # 4
    TOP_RIGHT = POSITION.TOP | POSITION.RIGHT  # 6
    LEFT = POSITION.LEFT  # 1
    RIGHT = POSITION.RIGHT  # 2
    BOTTOM_LEFT = POSITION.BOTTOM | POSITION.LEFT  # 9
    BOTTOM = POSITION.BOTTOM  # 8
    BOTTOM_RIGHT = POSITION.BOTTOM | POSITION.RIGHT  # 10
    OUTER_TOP_LEFT = POSITION.TOP | POSITION.LEFT | POSITION.OUTER  # 21
    OUTER_TOP = POSITION.TOP | POSITION.OUTER  # 20
    OUTER_TOP_RIGHT = POSITION.TOP | POSITION.RIGHT | POSITION.OUTER  # 22
    OUTER_LEFT = POSITION.LEFT | POSITION.OUTER  # 17
    OUTER_RIGHT = POSITION.RIGHT | POSITION.OUTER  # 18
    OUTER_BOTTOM_LEFT = POSITION.BOTTOM | POSITION.LEFT | POSITION.OUTER  # 25
    OUTER_BOTTOM = POSITION.BOTTOM | POSITION.OUTER  # 24
    OUTER_BOTTOM_RIGHT = POSITION.BOTTOM | POSITION.RIGHT | POSITION.OUTER  # 26


ALIGN = _Align()
