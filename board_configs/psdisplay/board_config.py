"""
Board configuration for PyScript.
"""

from displaysys.psdisplay import PSDevices, PSDisplay
import eventsys

width = 320
height = 480

display_drv = PSDisplay("display_canvas", width, height)

broker = eventsys.Broker()

devices_drv = PSDevices("display_canvas", display_drv)

events_dev = broker.create(
    type=eventsys.QUEUE,
    read=devices_drv.read,
    data=display_drv,
)

broker.register_quit_cleanup(display_drv)

display_drv.fill(0)
