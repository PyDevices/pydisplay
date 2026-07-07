"""
Combination board configuration for desktop, pyscript and jupyter notebook platforms.
If you are running pydisplay on a microcontroller, you will need to get or create a
board_config.py file that is specific to your hardware from:

https://github.com/PyDevices/pydisplay/tree/main/board_configs
"""

# False: default multimer.Timer (MCU, desktop Linux, etc.)
# True: multimer.AsyncTimer — PyScript and asyncio-native apps
TIMER_ASYNC = False

# ILI9341 2.8" panel (portrait native resolution; apps may set rotation=90 for landscape)
width = 240
height = 320
rotation = 0
scale = 2.0

touch_dev = None


_DISPLAY_REFRESH_MS = 33


def _wire_display_refresh(broker, display_drv, *, async_=False, period=_DISPLAY_REFRESH_MS):
    """Drive display refresh from the broker's shared timer.

    The broker owns the timer (see ``eventsys.Broker.on_tick``); the display only
    provides ``show()``. Quit tears the shared timer down after the display is
    released.
    """
    # Keep the refresh subscription handle on the broker so a GUI layer (e.g.
    # LVGL via display_driver) can take over presenting frames itself.
    broker.display_refresh = broker.on_tick(display_drv.show, period=period, async_=async_)
    broker.register_quit_cleanup(display_drv, after=broker.stop_timer)


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
    _wire_display_refresh(broker, display_drv, async_=True)
elif _jn:
    # Running in Jupyter Notebook
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
    _wire_display_refresh(broker, display_drv, async_=TIMER_ASYNC)
else:
    # Running on the desktop
    import sys

    _DESKTOP_PLATFORMS = frozenset(
        ("linux", "darwin", "win32", "unix", "webassembly", "emscripten")
    )
    _impl = sys.implementation.name
    if _impl in ("micropython", "circuitpython") and sys.platform not in _DESKTOP_PLATFORMS:
        print(
            "board_config: default board_config.py from lib/ is for desktop "
            "displaysys only.\n"
            "On a microcontroller, copy a board_config.py for your hardware "
            "into the current working directory (the parent of lib/).\n"
            "Download board configs from:\n"
            "  https://github.com/PyDevices/pydisplay/tree/main/board_configs"
        )

    import eventsys

    try:
        # This should load for CPython
        from displaysys.pgdisplay import PGDisplay as DTDisplay
        from displaysys.pgdisplay import get_events
    except ImportError:
        # This should load for MicroPython on the desktop
        from displaysys.sdldisplay import SDLDisplay as DTDisplay
        from displaysys.sdldisplay import get_events

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
    _wire_display_refresh(broker, display_drv, async_=TIMER_ASYNC)

if _ps:
    TIMER_ASYNC = True

display_drv.fill(0)
