"""
Combination board configuration for desktop, pyscript and jupyter notebook platforms.
If you are running pydisplay on a microcontroller, you will need to get or create a
board_config.py file that is specific to your hardware from:

https://github.com/PyDevices/pydisplay/tree/main/board_configs
"""

# False: default multimer.Timer (MCU, desktop Linux, etc.)
# True: multimer.aio.Timer — PyScript and asyncio-native apps
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
    from displaysys.psdisplay import PSDisplay, PSTouch
    from eventsys import devices

    display_drv = PSDisplay("display_canvas", width, height)

    broker = devices.Broker()

    touch_drv = PSTouch("display_canvas")

    touch_dev = broker.create_device(
        type=devices.types.TOUCH,
        read=touch_drv.get_mouse_pos,
        data=display_drv,
    )
elif _jn:
    # Running in Jupyter Notebook
    from displaysys.jndisplay import JNDisplay, JNTouch
    from eventsys import devices

    TIMER_ASYNC = True

    broker = devices.Broker()

    display_drv = JNDisplay(width, height)

    touch_drv = JNTouch(display_drv)

    touch_dev = broker.create_device(
        type=devices.types.TOUCH,
        read=touch_drv.get_mouse_pos,
        data=display_drv,
    )
else:
    # Running on the desktop
    import sys

    from eventsys import devices

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

    broker = devices.Broker()

    events_dev = broker.create_device(
        type=devices.types.QUEUE,
        read=get,
        data=display_drv,
        # data2=events.filter,
    )

if _ps:
    TIMER_ASYNC = True

display_drv.fill(0)
