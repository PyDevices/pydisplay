"""
Board configuration for Jupyter Notebook.
"""

from displaysys.jndisplay import JNDevices, JNDisplay
from eventsys import devices

TIMER_ASYNC = True

width = 320
height = 480

broker = devices.Broker()

display_drv = JNDisplay(width, height)

devices_drv = JNDevices(display_drv)

events_dev = broker.create_device(
    type=devices.types.QUEUE,
    read=devices_drv.read,
    data=display_drv,
)

display_drv.fill(0)
