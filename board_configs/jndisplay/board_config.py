"""
Board configuration for Jupyter Notebook.
"""

from displaysys.jndisplay import JNDisplay
from eventsys import devices

width = 320
height = 480

broker = devices.Broker()

display_drv = JNDisplay(width, height)

display_drv.fill(0)
