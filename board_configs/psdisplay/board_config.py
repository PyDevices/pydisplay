"""
Board configuration for PyScript.
"""

from displaysys.psdisplay import PSDevices, PSDisplay
from eventsys import devices

width = 320
height = 480

display_drv = PSDisplay("display_canvas", width, height)

broker = devices.Broker()

devices_drv = PSDevices("display_canvas")

events_dev = broker.create_device(
    type=devices.types.QUEUE,
    read=devices_drv.read,
    data=display_drv,
)

display_drv.fill(0)
