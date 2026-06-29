"""
Board configuration for PyScript.
"""

from add_ons.quit_handler import wire_display_quit
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

wire_display_quit(broker)

display_drv.fill(0)
