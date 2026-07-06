"""
Combination board configuration for desktop, pyscript and jupyter notebook platforms.
If you are running pydisplay on a microcontroller, you will need to get or create a
board_config.py file that is specific to your hardware from:

https://github.com/PyDevices/pydisplay/tree/main/board_configs
"""

# False: default multimer.Timer (MCU, desktop Linux, etc.)
# True: multimer.AsyncTimer — PyScript and asyncio-native apps
TIMER_ASYNC = False

width = 640
height = 480
rotation = 0
scale = 1.0

touch_dev = None


def _attach_timer_to_broker(broker, *, async_=False, tick_ms=10):
    from multimer import AsyncTimer, Timer, ticks_add, ticks_diff, ticks_ms

    TimerClass = AsyncTimer if async_ else Timer

    callbacks = []
    timer = TimerClass(-1)

    class _BrokerTimerSubscription:
        def __init__(self, entry):
            self._entry = entry

        def deinit(self):
            entry = self._entry
            if entry is None:
                return
            self._entry = None
            try:
                callbacks.remove(entry)
            except ValueError:
                pass

    def _on_tick(timer_obj):
        now = ticks_ms()
        for entry in tuple(callbacks):
            if ticks_diff(entry[2], now) > 0:
                continue
            entry[2] = ticks_add(now, entry[1])
            entry[0](timer_obj)

    def on_tick(callback, *, period):
        entry = [callback, int(period), ticks_add(ticks_ms(), int(period))]
        callbacks.append(entry)
        return _BrokerTimerSubscription(entry)

    def stop_timer():
        callbacks[:] = []
        timer.deinit()

    timer.init(mode=TimerClass.PERIODIC, period=tick_ms, callback=_on_tick)
    broker._timer = timer
    broker.on_tick = on_tick
    broker.stop_timer = stop_timer
    return timer


def _share_broker_timer_with_display(broker, display_drv, *, async_=False, period=33):
    if not hasattr(broker, "on_tick"):
        _attach_timer_to_broker(broker, async_=async_)

    display_timer = getattr(display_drv, "_timer", None)
    if display_timer is not None:
        display_timer.deinit()

    display_drv._timer = broker.on_tick(display_drv._auto_refresh, period=period)


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
    _share_broker_timer_with_display(broker, display_drv, async_=True)
    broker.register_quit_cleanup(display_drv, after=broker.stop_timer)
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
    _share_broker_timer_with_display(broker, display_drv, async_=TIMER_ASYNC)
    broker.register_quit_cleanup(display_drv, after=broker.stop_timer)
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
    _share_broker_timer_with_display(broker, display_drv, async_=TIMER_ASYNC)
    broker.register_quit_cleanup(display_drv, after=broker.stop_timer)

if _ps:
    TIMER_ASYNC = True

display_drv.fill(0)
