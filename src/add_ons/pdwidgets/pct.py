# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`pdwidgets.pct`
====================================================
Classes that dynamically calculate the percentage of the width and height of a Widget
"""


class Height:
    """
    A class that dynamically calculates the percentage of the height of a Widget

    Args:
        percent (int | float): The percentage of the height of the widget
        widget (Widget): The widget whose height will be used to calculate the percentage

    Raises:
        ValueError: If the percent is not between 0 and 100
        AttributeError: If the widget has no attribute 'area'

    Returns:
        (int): The calculated percentage of the height of the widget

    Usage:
        import pdwidgets as pd
        ...
        widget = pd.Widget(parent, h=100)
        my_height = pd.pct.Height(50, widget)
        print(my_height)  # 50
        widget.height = 200
        print(my_height)  # 100
    """

    def __init__(self, percent, widget):
        if not (0 <= percent <= 100):
            raise ValueError(f"{self.__class__.__name__}: percent must be between 0 and 100")
        if not hasattr(widget, "area"):
            raise AttributeError(f"{self.__class__.__name__}: widget has no attribute 'area'")
        self._percent = percent
        self._widget = widget

    __hash__ = None

    def __eq__(self, other):
        return float(self) == other

    def __float__(self):
        return self._percent * self._widget.area.h / 100

    def __repr__(self):
        return str(float(self))

    def __add__(self, other):
        return float(self) + other

    def __sub__(self, other):
        return float(self) - other

    def __mul__(self, other):
        return float(self) * other

    def __truediv__(self, other):
        return float(self) / other

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return -self.__sub__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return other / float(self)

    def __int__(self):
        return int(float(self))


class Width:
    """
    A class that dynamically calculates the percentage of the width of a Widget

    Args:
        percent (int | float): The percentage of the width of the widget
        widget (Widget): The widget whose width will be used to calculate the percentage

    Raises:
        ValueError: If the percent is not between 0 and 100
        AttributeError: If the widget has no attribute 'area'

    Returns:
        (int): The calculated percentage of the width of the widget

    Usage:
        import pdwidgets as pd
        ...
        widget = pd.Widget(parent, w=100)
        my_width = pd.pct.Width(50, widget)
        print(my_width)  # 50
        widget.width = 200
        print(my_width)  # 100
    """

    def __init__(self, percent, widget):
        if not (0 <= percent <= 100):
            raise ValueError(f"{self.__class__.__name__}: percent must be between 0 and 100")
        if not hasattr(widget, "area"):
            raise AttributeError(f"{self.__class__.__name__}: widget has no attribute 'area'")
        self._percent = percent
        self._widget = widget

    __hash__ = None

    def __eq__(self, other):
        return float(self) == other

    def __float__(self):
        return self._percent * self._widget.area.w / 100

    def __repr__(self):
        return str(float(self))

    def __add__(self, other):
        return float(self) + other

    def __sub__(self, other):
        return float(self) - other

    def __mul__(self, other):
        return float(self) * other

    def __truediv__(self, other):
        return float(self) / other

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return -self.__sub__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return other / float(self)

    def __int__(self):
        return int(float(self))
