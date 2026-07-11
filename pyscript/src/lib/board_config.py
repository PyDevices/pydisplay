"""
Combination board configuration for desktop, pyscript and jupyter notebook platforms.
If you are running pydisplay on a microcontroller, you will need to get or create a
board_config.py file that is specific to your hardware from:

https://github.com/PyDevices/pydisplay/tree/main/board_configs
"""

from displaysys import env_bool

# Default timer mode for PG/SDL desktop when PYDISPLAY_TIMER_ASYNC is unset.
# PyScript and Jupyter always use asyncio timers (see branches below).
DEFAULT_TIMER_ASYNC = False

# Default portrait panel (320x480). Games scale layout for taller/wider panels
# (e.g. 480x800, 720x720) via display_drv.width / height.
width = 320
height = 480
rotation = 0
scale = 2

_DESKTOP_PLATFORMS = frozenset(("linux", "darwin", "win32", "unix", "webassembly", "emscripten"))


def _host_kind():
    try:
        import pyscript  # noqa: F401

        return "pyscript"
    except ImportError:
        pass
    try:
        get_ipython()  # noqa: F821
        return "jupyter"
    except NameError:
        return "desktop"


def _make_runtime(display, host_read, *, timer_async):
    import eventsys

    return eventsys.Runtime(
        display=display,
        host_read=host_read,
        timer_async=timer_async,
    )


def _warn_embedded_default_board():
    import sys

    impl = sys.implementation.name
    if impl in ("micropython", "circuitpython") and sys.platform not in _DESKTOP_PLATFORMS:
        print(
            "board_config: default board_config.py from lib/ is for desktop "
            "displaysys only.\n"
            "On a microcontroller, copy a board_config.py for your hardware "
            "into the current working directory (the parent of lib/).\n"
            "Download board configs from:\n"
            "  https://github.com/PyDevices/pydisplay/tree/main/board_configs"
        )


def _desktop_display(title):
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
        title=title,
        scale=scale,
    )
    return display_drv, get_events


_host = _host_kind()

if _host == "pyscript":
    from displaysys.psdisplay import PSDevices, PSDisplay

    display_drv = PSDisplay("display_canvas", width, height)
    devices_drv = PSDevices("display_canvas", display_drv)
    runtime = _make_runtime(display_drv, devices_drv.read, timer_async=True)
elif _host == "jupyter":
    from displaysys.jndisplay import JNDevices, JNDisplay

    display_drv = JNDisplay(width, height)
    devices_drv = JNDevices(display_drv)
    runtime = _make_runtime(display_drv, devices_drv.read, timer_async=True)
else:
    import sys

    _warn_embedded_default_board()
    display_drv, get_events = _desktop_display(f"{sys.implementation.name} on {sys.platform}")
    runtime = _make_runtime(
        display_drv,
        get_events,
        timer_async=env_bool("PYDISPLAY_TIMER_ASYNC", DEFAULT_TIMER_ASYNC),
    )

display_drv.fill(0)
