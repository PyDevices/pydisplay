"""
Board configuration for Jupyter Notebook.
"""

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

broker.display_refresh = broker.on_tick(display_drv.show, period=33, async_=TIMER_ASYNC)
broker.register_quit_cleanup(display_drv, after=broker.stop_timer)

display_drv.fill(0)
