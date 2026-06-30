# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`graphics._area`
====================================================
Area class for defining rectangular areas.
"""


class Area:
    """
    Represents a rectangular area defined by its position and dimensions.

    Attributes:
        x (int | float): The x-coordinate of the top-left corner of the area.
        y (int | float): The y-coordinate of the top-left corner of the area.
        w (int | float): The width of the area.
        h (int | float): The height of the area.

    Methods:
        contains(x, y): Checks if the specified point is contained within the area.
        contains_area(other): Checks if the specified area is contained within the area.
        intersects(other): Checks if the current Area object intersects with another Area object.
        touches_or_intersects(other): Checks if the current Area object touches or intersects with another Area object.
        shift(dx=0, dy=0): Returns a new Area shifted by the specified amount in the x and y directions.
        clip(other): Clips the current Area object to the specified Area object.

    Special Methods:
        __eq__(other): Checks if the current Area object is equal to another Area object.
        __ne__(other): Checks if the current Area object is not equal to another Area object.
        __add__(other): Computes the union of the current Area object and another Area object.
        __iter__(): Returns an iterator over the elements of the Area object.
        __repr__(): Returns a string representation of the Area object.
        __str__(): Returns a string representation of the Area object.
    """

    __hash__ = None

    def __init__(self, x, y=None, w=None, h=None):
        """
        Initializes a new instance of the Area class.

        Args:
            x (int | float | tuple): The x-coordinate of the top-left corner of the area or
                a tuple containing the x, y, w, and h coordinates of the area.
            y (int | float): The y-coordinate of the top-left corner of the area.
            w (int | float): The width of the area.
            h (int | float): The height of the area.
        """
        if isinstance(x, tuple):
            x, y, w, h = x
        if y is None or w is None or h is None:
            raise ValueError("Invalid arguments")
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, x, y=None):
        """
        Checks if the specified point is contained within the area.

        Args:
            x (int | tuple): The x-coordinate of the point to check
                or a tuple containing the x and y coordinates of the point.
            y (int): The y-coordinate of the point to check.

        Returns:
            (bool): True if the point is contained within the area, False otherwise.
        """
        if isinstance(x, tuple):
            x, y = x
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    def contains_area(self, other):
        """
        Checks if the specified area is contained within the area.

        Args:
            other (Area): The other area to check.

        Returns:
            (bool): True if the other area is contained within the area, False otherwise.
        """
        return (
            self.x <= other.x
            and self.y <= other.y
            and self.x + self.w >= other.x + other.w
            and self.y + self.h >= other.y + other.h
        )

    def intersects(self, other):
        """
        Checks if the current Area object intersects with another Area object.

        Args:
            other (Area): The other Area object to check for overlap.

        Returns:
            (bool): True if the two Area objects intersect, False otherwise.
        """
        if self.x + self.w <= other.x or other.x + other.w <= self.x:
            return False
        return not (self.y + self.h <= other.y or other.y + other.h <= self.y)

    def touches_or_intersects(self, other):
        """
        Checks if the current Area object touches or intersects with another Area object.

        Args:
            other (Area): The other Area object to check for overlap or touch.

        Returns:
            (bool): True if the two Area objects touch or intersect, False otherwise.
        """
        if self.x + self.w < other.x or other.x + other.w < self.x:
            return False
        return not (self.y + self.h < other.y or other.y + other.h < self.y)

    def shift(self, dx=0, dy=0):
        """
        Returns a new Area shifted by the specified amount in the x and y directions.

        Args:
            dx (int | float): The amount to shift the area in the x direction.
            dy (int | float): The amount to shift the area in the y direction.

        Returns:
            (Area): A new Area object shift by the specified amount in the x and y directions.
        """
        return Area(self.x + dx, self.y + dy, self.w, self.h)

    def clip(self, other):
        """
        Clips the current Area object to the specified Area object.

        Args:
            other (Area): The other Area object to clip to.

        Returns:
            (Area): A new Area object representing the clipped area.
        """
        x = max(self.x, other.x)
        y = max(self.y, other.y)
        w = min(self.x + self.w, other.x + other.w) - x
        h = min(self.y + self.h, other.y + other.h) - y
        return Area(x, y, w, h)

    def offset(self, d1, d2=None, d3=None, d4=None):
        """
        Returns a new Area offset by the specified amount(s).

        If only one argument is provided, it is used as the offset in all 4 directions.
        If two arguments are provided, the first is used as the offset in the x direction and the second as the offset in the y direction.
        If three arguments are provided, they are used as the offsets in the left, top/bottom, and right directions, respectively.
        If four arguments are provided, they are used as the offsets in the left, top, right, and bottom directions, respectively.

        Args:
            d1 (int | float): The offset in the x direction or the offset in all 4 directions.
            d2 (int | float): The offset in the y direction or the offset in the top/bottom direction.
            d3 (int | float): The offset in the right direction.
            d4 (int | float): The offset in the bottom direction.

        Returns:
            (Area): A new Area object offset by the specified amount(s).
        """
        if d2 is None:
            d2 = d3 = d4 = d1
        elif d3 is None:
            d3 = d1
            d4 = d2
        elif d4 is None:
            d4 = d2
        return Area(self.x - d1, self.y - d2, self.w + d1 + d3, self.h + d2 + d4)

    def inset(self, d1, d2=None, d3=None, d4=None):
        """
        Returns a new Area inset by the specified amount(s).

        If only one argument is provided, it is used as the inset in all 4 directions.
        If two arguments are provided, the first is used as the inset in the x direction and the second as the inset in the y direction.
        If three arguments are provided, they are used as the insets in the left, top/bottom, and right directions, respectively.
        If four arguments are provided, they are used as the insets in the left, top, right, and bottom directions, respectively.

        Args:
            d1 (int | float): The inset in the x direction or the inset in all 4 directions.
            d2 (int | float): The inset in the y direction or the inset in the top/bottom direction.
            d3 (int | float): The inset in the right direction.
            d4 (int | float): The inset in the bottom direction.

        Returns:
            (Area): A new Area object inset by the specified amount(s).
        """
        if d2 is None:
            d2 = d3 = d4 = d1
        elif d3 is None:
            d3 = d1
            d4 = d2
        elif d4 is None:
            d4 = d2
        return Area(self.x + d1, self.y + d2, self.w - d1 - d3, self.h - d2 - d4)

    def __eq__(self, other):
        """
        Checks if the current Area object is equal to another Area object.

        Args:
            other (Area): The other Area object to compare with.

        Returns:
            (bool): True if the two Area objects are equal, False otherwise.
        """
        return self.x == other.x and self.y == other.y and self.w == other.w and self.h == other.h

    def __ne__(self, other):
        """
        Checks if the current Area object is not equal to another Area object.

        Args:
            other (Area): The other Area object to compare with.

        Returns:
            (bool): True if the two Area objects are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def __add__(self, other):
        """
        Computes the union of the current Area object and another Area object.

        Args:
            other (Area): The other Area object to compute the union with.

        Returns:
            (Area): A new Area object representing the union of the two areas.
        """
        return Area(
            min(self.x, other.x),
            min(self.y, other.y),
            max(self.x + self.w, other.x + other.w) - min(self.x, other.x),
            max(self.y + self.h, other.y + other.h) - min(self.y, other.y),
        )

    def __iter__(self):
        """
        Returns an iterator over the elements of the Area object.

        Returns:
            (iterator): An iterator over the elements of the Area object.
        """
        return iter((self.x, self.y, self.w, self.h))

    def __repr__(self):
        """
        Returns a string representation of the Area object.

        Returns:
            (str): A string representation of the Area object.
        """
        return f"Area({self.x}, {self.y}, {self.w}, {self.h})"

    def __str__(self):
        """
        Returns a string representation of the Area object.

        Returns:
            (str): A string representation of the Area object.
        """
        return f"Area({self.x}, {self.y}, {self.w}, {self.h})"
