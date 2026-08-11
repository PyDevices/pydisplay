# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""Host auto-selection for desktop-like displaysys backends.

Selects ``PSDisplay`` / ``JNDisplay`` / ``WinDisplay``→``PGDisplay``→
``SDLDisplay`` (or Android ``AndroidSDLDisplay``) from the runtime host so
board configs stay MCU-shaped wiring only. Explicit boards import a backend
directly; this factory is convenience only.

Returns the display driver directly. Desktop drivers expose ``get_events`` for
``Runtime(host_read=...)`` and ``requires_async_timer`` for the timer default.
"""

import sys

__all__ = ["AutoDisplay", "host_kind"]


def host_kind():
    """Return ``"android"``, ``"pyscript"``, ``"jupyter"``, or ``"desktop"``."""
    if sys.platform == "android":
        return "android"
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
    """Construct a host-appropriate display driver.

    Args:
        width, height, rotation, scale, title: Forwarded to PG/SDL constructors
            (PS/JN ignore rotation/scale/title as their APIs dictate).
        canvas_id: PyScript canvas DOM id for the primary ``PSDisplay``.
        quiet: Suppress driver init chatter when True.

    Returns:
        A ``PSDisplay``, ``JNDisplay``, ``WinDisplay``, ``PGDisplay``, or
        ``SDLDisplay`` with ``get_events`` and ``requires_async_timer`` set for
        board_config wiring.
    """
    host = host_kind()

    if host == "pyscript":
        from displaysys.psdisplay import PSDisplay

        return PSDisplay(canvas_id, width, height, quiet=quiet)

    if host == "jupyter":
        from displaysys.jndisplay import JNDisplay

        return JNDisplay(width, height, quiet=quiet)

    if host == "android":
        import usdl2

        from displaysys.androidsdl import AndroidSDLDisplay

        # Do not use SDL_WINDOW_FULLSCREEN_DESKTOP: it toggles immersive mode after
        # the Activity SurfaceView/GL buffers are created, and Android then rejects
        # presents (BLASTBufferQueue size mismatch → black screen after splash).
        # buildozer.spec keeps fullscreen=0; SHOWN + HIGHDPI matches that surface.
        # AndroidSDLDisplay locks Activity orientation from logical aspect.
        return AndroidSDLDisplay(
            width=width,
            height=height,
            rotation=rotation,
            title=title,
            scale=scale,
            quiet=quiet,
            window_flags=(usdl2.SDL_WINDOW_SHOWN | usdl2.SDL_WINDOW_ALLOW_HIGHDPI),
        )

    if sys.platform == "win32":
        try:
            from displaysys.windisplay import WinDisplay

            return WinDisplay(
                width=width,
                height=height,
                rotation=rotation,
                title=title,
                scale=scale,
                quiet=quiet,
            )
        except Exception:
            pass
        # pygame / SDL fallback: SDL2 WASAPI glitches with pygame small-chunk
        # playback; DirectSound does not. Must land before PGDisplay.pg.init().
        from displaysys import env_get, env_set

        if env_get("SDL_AUDIODRIVER") is None:
            env_set("SDL_AUDIODRIVER", "directsound")

    try:
        from displaysys.pgdisplay import PGDisplay
    except Exception:
        from displaysys.sdldisplay import SDLDisplay

        return SDLDisplay(
            width=width,
            height=height,
            rotation=rotation,
            title=title,
            scale=scale,
            quiet=quiet,
        )

    return PGDisplay(
        width=width,
        height=height,
        rotation=rotation,
        title=title,
        scale=scale,
        quiet=quiet,
    )
