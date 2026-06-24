"""
Board configuration for PyScript.
"""

from displaysys.psdisplay import PSDisplay, PSKeys, PSTouch
from eventsys import devices

width = 320
height = 480

display_drv = PSDisplay("display_canvas", width, height)

broker = devices.Broker()

touch_drv = PSTouch("display_canvas")

touch_dev = broker.create_device(
    type=devices.types.TOUCH,
    read=touch_drv.get_mouse_pos,
    data=display_drv,
)

keys_drv = PSKeys("display_canvas")

keys_dev = broker.create_device(
    type=devices.types.QUEUE,
    read=keys_drv.read,
    data=display_drv,
)

display_drv.fill(0)
