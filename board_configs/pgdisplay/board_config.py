"""
Board configuration for PyGame.
"""

import sys

from displaysys.pgdisplay import PGDisplay as DTDisplay
from displaysys.pgdisplay import get_events
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
    read=get_events,
    data=display_drv,
    # data2=events.filter,
)

broker.register_quit_cleanup(display_drv)

display_drv.fill(0)
