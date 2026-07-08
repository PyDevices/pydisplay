"""
Board configuration for PyScript.
"""

from displaysys.psdisplay import PSDevices, PSDisplay
import eventsys

width = 320
height = 480

display_drv = PSDisplay("display_canvas", width, height)
devices_drv = PSDevices("display_canvas", display_drv)

runtime = eventsys.Runtime(
    display=display_drv,
    host_read=devices_drv.read,
    timer_async=True,
)

display_drv.fill(0)
