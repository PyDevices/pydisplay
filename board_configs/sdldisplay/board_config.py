"""
Combination board configuration for desktop, pyscript and jupyter notebook platforms.
"""

import sys

from add_ons.quit_handler import wire_display_quit
from displaysys.sdldisplay import SDLDisplay as DTDisplay
from displaysys.sdldisplay import poll
import eventsys

width = 320
height = 480
rotation = 0
scale = 2.0

display_drv = DTDisplay(
    width=width,
    height=height,
    rotation=rotation,
    title=f"{sys.implementation.name} on {sys.platform}",
    scale=scale,
)

broker = eventsys.Broker()

events_dev = broker.create(
    type=eventsys.QUEUE,
    read=poll,
    data=display_drv,
    # data2=events.filter,
)

wire_display_quit(broker)

display_drv.fill(0)
