"""
Combination board configuration for desktop, pyscript and jupyter notebook platforms.
If you are running pydisplay on a microcontroller, you will need to get or create a
board_config.py file that is specific to your hardware from:

https://github.com/PyDevices/pydisplay/tree/main/board_configs
"""

# Default portrait panel (320x480). Games scale layout for taller/wider panels
# (e.g. 480x800, 720x720) via display_drv.width / height.
width = 320
height = 480
rotation = 0
scale = 2


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
    from displaysys.psdisplay import PSDevices, PSDisplay
    import eventsys

    display_drv = PSDisplay("display_canvas", width, height)
    devices_drv = PSDevices("display_canvas", display_drv)
    runtime = eventsys.Runtime(
        display=display_drv,
        host_read=devices_drv.read,
        timer_async=True,
    )
elif _jn:
    from displaysys.jndisplay import JNDevices, JNDisplay
    import eventsys

    display_drv = JNDisplay(width, height)
    devices_drv = JNDevices(display_drv)
    runtime = eventsys.Runtime(
        display=display_drv,
        host_read=devices_drv.read,
        timer_async=True,
    )
else:
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
        from displaysys.pgdisplay import PGDisplay as DTDisplay
        from displaysys.pgdisplay import get_events
    except ImportError:
        from displaysys.sdldisplay import SDLDisplay as DTDisplay
        from displaysys.sdldisplay import get_events

    display_drv = DTDisplay(
        width=width,
        height=height,
        rotation=rotation,
        title=f"{sys.implementation.name} on {sys.platform}",
        scale=scale,
    )
    runtime = eventsys.Runtime(display=display_drv, host_read=get_events, timer_async=True)

display_drv.fill(0)
