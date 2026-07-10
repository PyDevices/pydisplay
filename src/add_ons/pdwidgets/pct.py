# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`pdwidgets.pct`
====================================================
Classes that dynamically calculate a percentage of a Widget's width or height.

``Width``/``Height`` are lightweight value objects: pass one as a widget's ``w``
or ``h`` and it tracks the reference widget's size, so a child stays at (say)
50% of its parent even after the parent is resized.

Performance
-----------
The value is read straight from ``widget.width`` / ``widget.height`` (plain
``int(self._w)`` / ``int(self._h)`` accessors) rather than constructing a full
``widget.area`` ``Area`` object on every access, and the computed result is
cached and only recomputed when the reference dimension actually changes. This
keeps the common case (repeated reads while the widget is not resizing) down to
a single attribute read and comparison, which matters on MicroPython where the
old design allocated an ``Area`` and re-multiplied on every arithmetic op and
comparison.
"""


class _Percent:
    """Base for :class:`Width` / :class:`Height`: a cached percentage of a widget dimension."""

    # Value-like and dynamic, so it is intentionally unhashable (mirrors
    # ``graphics.Area``); it is never used as a set/dict key.
    __hash__ = None

    def __init__(self, percent, widget):
        if not (0 <= percent <= 100):
            raise ValueError(f"{self.__class__.__name__}: percent must be between 0 and 100")
        if not hasattr(widget, "area"):
            raise AttributeError(f"{self.__class__.__name__}: widget has no attribute 'area'")
        self._percent = percent
        self._widget = widget
        self._cache_dim = None
        self._cache_val = 0.0

    def _dimension(self):
        """Return the current reference dimension (overridden by subclasses)."""
        raise NotImplementedError

    def __float__(self):
        dim = self._dimension()
        if dim != self._cache_dim:
            self._cache_dim = dim
            self._cache_val = self._percent * dim / 100
        return self._cache_val

    def __eq__(self, other):
        return float(self) == other

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


class Height(_Percent):
    """
    A value object that tracks a percentage of a Widget's height.

    Args:
        percent (int | float): The percentage of the height of the widget (0-100).
        widget (Widget): The widget whose height drives the calculation.

    Raises:
        ValueError: If the percent is not between 0 and 100.
        AttributeError: If the widget has no attribute 'area'.

    Returns:
        (int): The calculated percentage of the height of the widget.

    Usage:
        import pdwidgets as pd
        ...
        widget = pd.Widget(parent, h=100)
        my_height = pd.pct.Height(50, widget)
        print(my_height)  # 50
        widget.height = 200
        print(my_height)  # 100
    """

    def _dimension(self):
        return self._widget.height


class Width(_Percent):
    """
    A value object that tracks a percentage of a Widget's width.

    Args:
        percent (int | float): The percentage of the width of the widget (0-100).
        widget (Widget): The widget whose width drives the calculation.

    Raises:
        ValueError: If the percent is not between 0 and 100.
        AttributeError: If the widget has no attribute 'area'.

    Returns:
        (int): The calculated percentage of the width of the widget.

    Usage:
        import pdwidgets as pd
        ...
        widget = pd.Widget(parent, w=100)
        my_width = pd.pct.Width(50, widget)
        print(my_width)  # 50
        widget.width = 200
        print(my_width)  # 100
    """

    def _dimension(self):
        return self._widget.width
