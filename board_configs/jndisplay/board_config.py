"""
Board configuration for Jupyter Notebook.
"""

from add_ons.quit_handler import wire_display_quit
from displaysys.jndisplay import JNDevices, JNDisplay
import eventsys

TIMER_ASYNC = True

width = 320
height = 480

broker = eventsys.Broker()

display_drv = JNDisplay(width, height)

devices_drv = JNDevices(display_drv)

events_dev = broker.create(
    type=eventsys.QUEUE,
    read=devices_drv.read,
    data=display_drv,
)

wire_display_quit(broker)

display_drv.fill(0)
