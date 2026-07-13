# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ._layout import _Layout


class Column(_Layout):
    """
    A container that stacks its children top-to-bottom with fixed spacing.

    Args:
        parent (Widget): The parent widget or screen that contains this column.
        x (int): The x-coordinate of the column.
        y (int): The y-coordinate of the column.
        w (int): The width of the column.
        h (int): The height of the column.
        align (int): The alignment of the column.
        align_to (Widget): The widget to align to.
        fg (int): The foreground color of the column.
        bg (int): The background color of the column.
        visible (bool): The visibility of the column.
        value (Any): User-assigned value of the column.
        padding (tuple): The padding on each side of the column.
        spacing (int): Gap in pixels inserted between children (default PAD).

    Usage:
        col = Column(screen, spacing=6)
        Label(col, value="One")
        Label(col, value="Two")
    """

    _vertical = True
