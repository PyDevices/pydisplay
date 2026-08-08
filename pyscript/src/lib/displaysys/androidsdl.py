# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""Android SDL display: Activity orientation from logical aspect, surface scale.

MCU-shaped contract: the app chooses orientation via panel size / ``rotation``
(logical ``width`` vs ``height``). The Activity is locked to that aspect;
tilting the phone does not change it — the user turns the device to match.
"""

from __future__ import annotations

import sys

import usdl2

from displaysys.sdldisplay import SDLDisplay, retcheck

__all__ = ["AndroidSDLDisplay"]

# android.content.pm.ActivityInfo
_ORIENTATION_LANDSCAPE = 0
_ORIENTATION_PORTRAIT = 1

_HINT_ORIENTATIONS = getattr(usdl2, "SDL_HINT_ORIENTATIONS", "SDL_IOS_ORIENTATIONS")


def _logical_size(width, height, rotation):
    """Return logical (w, h) for stored panel size + rotation degrees."""
    rot = int(rotation) % 360
    if ((rot // 90) & 0x1) == 0x1:
        return int(height), int(width)
    return int(width), int(height)


def _fit_scale_android(width, height, scale, desktop_w, desktop_h, chrome_w=0, chrome_h=0):
    """Keep board_config scale; ignore desktop chrome / usable-bounds shrink.

    On Android the Activity surface owns the window size — SDL letterboxes the
    logical panel via ``RenderSetLogicalSize``. Shrinking scale from
    ``GetDisplayUsableBounds`` only feeds a wrong CreateWindow aspect into
    SDL's orientation helper (e.g. 720x1280 -> 607x1080).
    """
    del width, height, desktop_w, desktop_h, chrome_w, chrome_h
    return 1.0 if scale <= 0 else float(scale)


def _set_orientation_hint(landscape):
    """Restrict SDL Android orientations to the locked aspect."""
    set_hint = getattr(usdl2, "SDL_SetHint", None)
    if set_hint is None:
        return
    value = "LandscapeLeft LandscapeRight" if landscape else "Portrait"
    try:
        set_hint(_HINT_ORIENTATIONS, value)
    except Exception:
        pass


def _set_activity_orientation(landscape):
    """Lock the Activity to fixed landscape or portrait (not SENSOR_*)."""
    if sys.platform != "android":
        return
    try:
        from jnius import autoclass
    except ImportError:
        return
    try:
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        if activity is None:
            return
        flag = _ORIENTATION_LANDSCAPE if landscape else _ORIENTATION_PORTRAIT
        activity.setRequestedOrientation(flag)
    except Exception:
        pass


class AndroidSDLDisplay(SDLDisplay):
    """``SDLDisplay`` for Android: aspect → Activity lock, no RenderCopyEx rotate."""

    def __init__(
        self,
        width=320,
        height=240,
        rotation=0,
        color_depth=16,
        title="SDL2 Display",
        scale=1.0,
        window_flags=usdl2.SDL_WINDOW_SHOWN,
        render_flags=usdl2.SDL_RENDERER_ACCELERATED | usdl2.SDL_RENDERER_PRESENTVSYNC,
        x=usdl2.SDL_WINDOWPOS_CENTERED,
        y=usdl2.SDL_WINDOWPOS_CENTERED,
        *,
        quiet=False,
    ):
        lw, lh = _logical_size(width, height, rotation)
        _set_orientation_hint(lw > lh)

        import displaysys.sdldisplay as _sdlmod

        prev_fit = _sdlmod.fit_scale_to_desktop
        _sdlmod.fit_scale_to_desktop = _fit_scale_android
        try:
            super().__init__(
                width=width,
                height=height,
                rotation=rotation,
                color_depth=color_depth,
                title=title,
                scale=scale,
                window_flags=window_flags,
                render_flags=render_flags,
                x=x,
                y=y,
                quiet=quiet,
            )
        finally:
            _sdlmod.fit_scale_to_desktop = prev_fit

        self._apply_activity_orientation()

    def _apply_activity_orientation(self, width=None, height=None):
        """Lock Activity to logical aspect (``width > height`` → landscape)."""
        w = int(self.width if width is None else width)
        h = int(self.height if height is None else height)
        landscape = w > h
        _set_orientation_hint(landscape)
        _set_activity_orientation(landscape)

    def _rotation_helper(self, value):
        """Recreate an upright buffer at the new logical size; lock Activity.

        Does not ``SDL_RenderCopyEx`` — phone orientation carries the aspect,
        matching a fixed SPI panel the user turns to view.
        """
        angle = (value % 360) - (self._rotation % 360)
        if angle == 0:
            return
        if abs(angle) % 180 == 0:
            new_w, new_h = self.width, self.height
        else:
            new_w, new_h = self.height, self.width

        self._apply_activity_orientation(new_w, new_h)

        temp = usdl2.SDL_CreateTexture(
            self._renderer,
            self._px_format,
            usdl2.SDL_TEXTUREACCESS_TARGET,
            new_w,
            new_h,
        )
        if not temp:
            raise RuntimeError("%s" % (usdl2.SDL_GetError(),))
        retcheck(usdl2.SDL_SetTextureBlendMode(temp, usdl2.SDL_BLENDMODE_NONE))
        retcheck(usdl2.SDL_SetRenderTarget(self._renderer, temp))
        retcheck(usdl2.SDL_SetRenderDrawColor(self._renderer, 0, 0, 0, 255))
        usdl2.SDL_RenderClear(self._renderer)
        retcheck(usdl2.SDL_SetRenderTarget(self._renderer, None))
        retcheck(usdl2.SDL_DestroyTexture(self._buffer))
        self._buffer = temp
        self._render_dirty = True
