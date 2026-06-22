# multimer types: all
"""
Test the Area return type of the shapes functions.

Shape functions return an Area object that represents the bounding box of the shape drawn.
This object can be used to optimize the display by redrawing only the area that has changed.

Area objects have the attributes x, y, w and h.  They may be added together, such as:
    area3 = area1 + area2

and may be unpacked, such as:
    x, y, w, h = area3
or as a function argument:
    rect(display_drv, *area3, 0x00FF)

"""

from board_config import display_drv
from graphics import rect, circle, ellipse


dirty = circle(display_drv, 120, 120, 50, 0xFF00, True)
dirty += ellipse(display_drv, 100, 85, 50, 30, 0x0FF0, True, 0b1111)
rect(display_drv, *dirty, 0x00FF)
display_drv.show()
