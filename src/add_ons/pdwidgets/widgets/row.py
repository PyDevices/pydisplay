# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
from ._layout import _Layout


class Row(_Layout):
    """
    A container that lays its children out left-to-right with fixed spacing.

    Args:
        parent (Widget): The parent widget or screen that contains this row.
        x (int): The x-coordinate of the row.
        y (int): The y-coordinate of the row.
        w (int): The width of the row.
        h (int): The height of the row.
        align (int): The alignment of the row.
        align_to (Widget): The widget to align to.
        fg (int): The foreground color of the row.
        bg (int): The background color of the row.
        visible (bool): The visibility of the row.
        value (Any): User-assigned value of the row.
        padding (tuple): The padding on each side of the row.
        spacing (int): Gap in pixels inserted between children (default PAD).

    Usage:
        row = Row(screen, spacing=6)
        Button(row, label="A")
        Button(row, label="B")
    """

    _vertical = False
