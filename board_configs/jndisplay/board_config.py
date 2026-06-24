"""
Board configuration for Jupyter Notebook.
"""

from displaysys.jndisplay import JNDisplay, JNTouch
from eventsys import devices

TIMER_ASYNC = True

width = 320
height = 480

broker = devices.Broker()

display_drv = JNDisplay(width, height)

touch_drv = JNTouch(display_drv)

touch_dev = broker.create_device(
    type=devices.types.TOUCH,
    read=touch_drv.get_mouse_pos,
    data=display_drv,
)

display_drv.fill(0)
