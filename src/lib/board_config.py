"""
Combination board configuration for desktop, pyscript and jupyter notebook platforms.
If you are running pydisplay on a microcontroller, you will need to get or create a
board_config.py file that is specific to your hardware from:

https://github.com/PyDevices/pydisplay/tree/main/board_configs
"""

# False: default multimer.Timer (MCU, desktop Linux, etc.)
# True: multimer.AsyncTimer — PyScript and asyncio-native apps
TIMER_ASYNC = False

width = 320
height = 480
rotation = 0
scale = 1.0

touch_dev = None

_ps = _jn = False
try:
    import pyscript

    _ps = True
except ImportError:
    try:
        get_ipython()
        _jn = True
    except NameError:
        pass

if _ps:
    # Running in PyScript
    from add_ons.quit_handler import wire_display_quit
    from displaysys.psdisplay import PSDevices, PSDisplay
    import eventsys

    display_drv = PSDisplay("display_canvas", width, height)

    broker = eventsys.Broker()

    devices_drv = PSDevices("display_canvas", display_drv)

    events_dev = broker.create(
        type=eventsys.QUEUE,
        read=devices_drv.read,
        data=display_drv,
    )
elif _jn:
    # Running in Jupyter Notebook
    from add_ons.quit_handler import wire_display_quit
    from displaysys.jndisplay import JNDevices, JNDisplay
    import eventsys

    TIMER_ASYNC = True

    broker = eventsys.Broker()

    display_drv = JNDisplay(width, height)

    devices_drv = JNDevices(display_drv)

    events_dev = broker.create(
        type=eventsys.QUEUE,
        read=devices_drv.read,
        data=display_drv,
    )
else:
    # Running on the desktop
    import sys

    from add_ons.quit_handler import wire_display_quit
    import eventsys

    try:
        # This should load for CPython
        from displaysys.pgdisplay import PGDisplay as DTDisplay
        from displaysys.pgdisplay import get
    except ImportError:
        # This should load for MicroPython on the desktop
        from displaysys.sdldisplay import SDLDisplay as DTDisplay
        from displaysys.sdldisplay import get

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
        read=get,
        data=display_drv,
        # data2=events.filter,
    )

if _ps:
    TIMER_ASYNC = True

wire_display_quit(broker)

display_drv.fill(0)
