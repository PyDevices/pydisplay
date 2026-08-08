# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""Host auto-selection for desktop-like displaysys backends.

Selects ``PSDisplay`` / ``JNDisplay`` / ``PGDisplay``→``SDLDisplay`` from the
runtime host so board configs stay MCU-shaped wiring only.
"""

__all__ = ["AutoDisplay", "AutoDisplayResult", "host_kind"]


class AutoDisplayResult:
    """Bundle returned by :func:`AutoDisplay`.

    Attributes:
        display: Concrete displaysys driver instance.
        host_read: Callable suitable for ``eventsys.Runtime(host_read=...)``.
        timer_async: Recommended default for ``Runtime(timer_async=...)``.
        host: ``"pyscript"``, ``"jupyter"``, or ``"desktop"``.
    """

    def __init__(self, display, host_read, timer_async, host):
        self.display = display
        self.host_read = host_read
        self.timer_async = timer_async
        self.host = host


def host_kind():
    """Return ``"pyscript"``, ``"jupyter"``, or ``"desktop"``."""
    try:
        import pyscript  # noqa: F401

        return "pyscript"
    except Exception:
        pass
    try:
        get_ipython()  # noqa: F821
        return "jupyter"
    except Exception:
        return "desktop"


def AutoDisplay(
    width=320,
    height=240,
    rotation=0,
    scale=1.0,
    title="displaysys",
    canvas_id="display_canvas",
    *,
    quiet=False,
):
    """Construct a host-appropriate display and matching ``host_read``.

    Args:
        width, height, rotation, scale, title: Forwarded to PG/SDL constructors
            (PS/JN ignore rotation/scale/title as their APIs dictate).
        canvas_id: PyScript canvas DOM id for the primary ``PSDisplay``.
        quiet: Suppress driver init chatter when True.

    Returns:
        AutoDisplayResult: ``.display``, ``.host_read``, ``.timer_async``, ``.host``.
    """
    host = host_kind()

    if host == "pyscript":
        from displaysys.psdisplay import PSDevices, PSDisplay

        display = PSDisplay(canvas_id, width, height, quiet=quiet)
        devices = PSDevices(canvas_id, display)
        return AutoDisplayResult(display, devices.read, True, host)

    if host == "jupyter":
        from displaysys.jndisplay import JNDevices, JNDisplay

        display = JNDisplay(width, height, quiet=quiet)
        devices = JNDevices(display)
        return AutoDisplayResult(display, devices.read, True, host)

    try:
        from displaysys.pgdisplay import PGDisplay, get_events
    except Exception:
        from displaysys.sdldisplay import SDLDisplay, get_events

        display = SDLDisplay(
            width=width,
            height=height,
            rotation=rotation,
            title=title,
            scale=scale,
            quiet=quiet,
        )
    else:
        display = PGDisplay(
            width=width,
            height=height,
            rotation=rotation,
            title=title,
            scale=scale,
            quiet=quiet,
        )

    return AutoDisplayResult(display, get_events, False, host)
