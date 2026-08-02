"""Board-specific runtime setup for pydisplay applications.

This module is the small bridge between your app and the host platform. In most
projects you import ``display_drv`` and ``runtime`` from ``board_config`` and
then build your UI around those objects. The exact backend changes from one
platform to another, but the app structure stays the same: create or update the
framebuffer, subscribe to input events, and keep the runtime alive with
``runtime.run_forever()``.

For desktop development the bundled module selects a windowed display backend
and a compatible event source, and exposes lazy ``DEVICES`` (including
``audio_out`` via SDL) the same way hardware boards do through
``board_devices``. On microcontrollers you typically copy a hardware-specific
``board_config.py`` from the micropython-hardware repo instead of using the
desktop default.

Desktop size / timer overrides (set before importing ``board_config``)::

    PYDISPLAY_WIDTH / PYDISPLAY_HEIGHT / PYDISPLAY_SCALE — integer panel size / scale
    PYDISPLAY_TIMER_ASYNC — truthy/falsey timer mode on PG/SDL desktop
"""

from displaysys import env_bool, env_float, env_int

# Default timer mode for PG/SDL desktop when PYDISPLAY_TIMER_ASYNC is unset.
# PyScript and Jupyter always use asyncio timers (see branches below).
DEFAULT_TIMER_ASYNC = False

# Default portrait panel (320x480). Games scale layout for taller/wider panels
# (e.g. 480x800, 720x720) via display_drv.width / height.
width = 320
height = 480
rotation = 0
scale = 2

width = env_int("PYDISPLAY_WIDTH", width)
height = env_int("PYDISPLAY_HEIGHT", height)
scale = env_float("PYDISPLAY_SCALE", scale)

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
        displays=[display],
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
            "  https://github.com/PyDevices/micropython-hardware/tree/main/board_configs"
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

# Hardware boards re-export this from board_devices via setup_devices.
# Desktop default starts empty; filled below to simulate board_devices.
DEVICES = frozenset()

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

    # Simulate board_devices: lazy audio_out via boarddev (SDL queued PCM).
    import boarddev

    class _DesktopDevices:
        DEVICES = frozenset({"audio_out"})

        @staticmethod
        def audio_out():
            from audiodev import AudioFormat
            from sdl2audio import audio_out as _sdl_audio_out

            # Gemini / common TTS default: 24 kHz mono s16le
            return _sdl_audio_out(AudioFormat(24000, 1, 16), queue_ms=150)

    DEVICES = _DesktopDevices.DEVICES
    boarddev.bind_lazy(globals(), _DesktopDevices)

display_drv.fill(0)
