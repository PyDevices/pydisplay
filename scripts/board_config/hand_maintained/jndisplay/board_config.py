"""
Board configuration for Jupyter Notebook.
"""

from displaysys.jndisplay import JNDevices, JNDisplay
import eventsys

width = 320
height = 480

display_drv = JNDisplay(width, height)
devices_drv = JNDevices(display_drv)

runtime = eventsys.Runtime(
    display=display_drv,
    host_read=devices_drv.read,
    timer_async=True,
)

display_drv.fill(0)
