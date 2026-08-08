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
import time

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
    """Do not let board_config scale drive CreateWindow on Android.

    A portrait ``720x1280`` at ``scale=2`` becomes ``1440x2560``. After a WIDE
    Activity lock, SDL still letterboxes into that stale tall size and content
    clips to the top-left. Window size follows the Activity SurfaceView; logical
    panel size is applied with ``RenderSetLogicalSize``.
    """
    del width, height, scale, desktop_w, desktop_h, chrome_w, chrome_h
    return 1.0


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


def _android_surface_sizes():
    """``(dm_wh, decor_wh)`` from the Activity, or ``(None, None)`` off-Android."""
    if sys.platform != "android":
        return None, None
    try:
        from jnius import autoclass
    except ImportError:
        return None, None
    try:
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        if activity is None:
            return None, None
        dm = activity.getResources().getDisplayMetrics()
        dm_wh = (int(dm.widthPixels), int(dm.heightPixels))
        if dm_wh[0] <= 0 or dm_wh[1] <= 0:
            dm_wh = None
        decor = activity.getWindow().getDecorView()
        decor_wh = (int(decor.getWidth()), int(decor.getHeight()))
        if decor_wh[0] <= 0 or decor_wh[1] <= 0:
            decor_wh = None
        return dm_wh, decor_wh
    except Exception:
        return None, None


def _pump_sdl(limit=64):
    """Drain SDL events so the Android video backend can apply surface resizes."""
    pump = getattr(usdl2, "SDL_PumpEvents", None)
    if pump is not None:
        try:
            pump()
        except Exception:
            pass
    event = usdl2.SDL_Event()
    for _ in range(limit):
        try:
            if not usdl2.SDL_PollEvent(event):
                break
        except Exception:
            break


def _sdl_output_size(window, renderer):
    """Best-effort SDL drawable size after an Android surface change."""
    get_out = getattr(usdl2, "SDL_GetRendererOutputSize", None)
    if get_out is not None and renderer is not None:
        try:
            size = get_out(renderer)
            if size and size[0] > 0 and size[1] > 0:
                return int(size[0]), int(size[1])
        except Exception:
            pass
    get_win = getattr(usdl2, "SDL_GetWindowSize", None)
    if get_win is not None and window is not None:
        try:
            size = get_win(window)
            if size and size[0] > 0 and size[1] > 0:
                return int(size[0]), int(size[1])
        except Exception:
            pass
    return None


def _aspect_ok(size, landscape):
    if size is None:
        return False
    w, h = size
    if landscape:
        return w > h
    return h >= w


def _wait_drawable_aspect(window, renderer, landscape, timeout_s=2.5):
    """Wait until SDL drawable aspect matches the locked Activity orientation.

    Non-fullscreen Android windows often settle to a short landscape size (e.g.
    ``2282x880`` while decor is ``2282x1080``) and never match decor — do not
    block on pixel alignment. Do **not** call ``SDL_SetWindowSize``.
    """
    deadline = time.time() + float(timeout_s)
    last_dm, last_decor = _android_surface_sizes()
    last_sdl = _sdl_output_size(window, renderer)
    stable = None
    stable_n = 0
    while time.time() < deadline:
        _pump_sdl()
        dm, decor = _android_surface_sizes()
        last_dm = dm or last_dm
        last_decor = decor or last_decor
        last_sdl = _sdl_output_size(window, renderer) or last_sdl
        if _aspect_ok(last_sdl, landscape) and (last_dm is None or _aspect_ok(last_dm, landscape)):
            if last_sdl == stable:
                stable_n += 1
                if stable_n >= 5:
                    return last_sdl
            else:
                stable = last_sdl
                stable_n = 1
        time.sleep(0.02)
    return last_sdl or last_decor or last_dm


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
        landscape = lw > lh
        _set_orientation_hint(landscape)
        # Lock before CreateWindow so the first SurfaceView matches aspect.
        _set_activity_orientation(landscape)

        import displaysys.sdldisplay as _sdlmod

        prev_fit = _sdlmod.fit_scale_to_desktop
        _sdlmod.fit_scale_to_desktop = _fit_scale_android
        try:
            # scale=1: CreateWindow uses logical panel size, not desktop scale.
            super().__init__(
                width=width,
                height=height,
                rotation=rotation,
                color_depth=color_depth,
                title=title,
                scale=1.0,
                window_flags=window_flags,
                render_flags=render_flags,
                x=x,
                y=y,
                quiet=quiet,
            )
        finally:
            _sdlmod.fit_scale_to_desktop = prev_fit

        # Requested scale kept for API/recorder; Android window sizing ignores it.
        self._scale = 1.0 if scale <= 0 else float(scale)
        self._orient_settle_until = 0.0
        self._await_drawable(landscape)

    def _await_drawable(self, landscape=None):
        """Pump until the SurfaceView/SDL drawable matches the locked aspect."""
        if sys.platform != "android":
            return
        if landscape is None:
            landscape = int(self.width) > int(self.height)
        _wait_drawable_aspect(
            getattr(self, "_window", None),
            getattr(self, "_renderer", None),
            landscape,
        )

    def _mark_orient_settle(self):
        """After Activity orientation, force recomposite until EGL presents stick.

        Non-fullscreen surfaces report the new size quickly, but the first
        ``RenderPresent`` calls are dropped; ``needs_refresh`` Present-only ticks
        then keep showing a black backbuffer. Re-running ``render()`` for a short
        window recovers.
        """
        self._orient_settle_until = time.time() + 2.5
        self._render_dirty = True

    def show(self, _timer=None) -> None:
        if time.time() < float(getattr(self, "_orient_settle_until", 0) or 0):
            self._render_dirty = True
        super().show(_timer)

    def _rebind_logical_texture(self, tex_w, tex_h):
        """Swap the target texture + logical size; keep the existing renderer.

        Non-fullscreen landscape drawables often stay at a short size.
        Destroying/recreating the renderer there blacks out presents;
        ``RenderSetLogicalSize`` + a new texture on the live renderer is enough.
        """
        old_tex = getattr(self, "_buffer", None)
        renderer = getattr(self, "_renderer", None)
        if renderer is None:
            raise RuntimeError("AndroidSDLDisplay: no renderer")
        if old_tex is not None:
            try:
                usdl2.SDL_DestroyTexture(old_tex)
            except Exception:
                pass
            self._buffer = None
        texture = usdl2.SDL_CreateTexture(
            renderer,
            self._px_format,
            usdl2.SDL_TEXTUREACCESS_TARGET,
            int(tex_w),
            int(tex_h),
        )
        if not texture:
            raise RuntimeError("%s" % (usdl2.SDL_GetError(),))
        retcheck(usdl2.SDL_SetTextureBlendMode(texture, usdl2.SDL_BLENDMODE_NONE))
        retcheck(usdl2.SDL_RenderSetLogicalSize(renderer, int(tex_w), int(tex_h)))
        self._buffer = texture
        self._render_dirty = True

    def init(self) -> None:
        """Wait for drawable aspect, then apply MCU logical size for letterboxing."""
        self._await_drawable()
        super().init()

    def _apply_activity_orientation(self, width=None, height=None):
        """Lock Activity to logical aspect (``width > height`` → landscape)."""
        w = int(self.width if width is None else width)
        h = int(self.height if height is None else height)
        landscape = w > h
        _set_orientation_hint(landscape)
        _set_activity_orientation(landscape)
        self._await_drawable(landscape)

    def _rotation_helper(self, value):
        """Lock Activity to the new aspect; rebind logical texture (no RenderCopyEx).

        Phone orientation carries the aspect (MCU-shaped). Does not require
        fullscreen — non-FS landscape SDL size may be shorter than decor.
        """
        angle = (value % 360) - (self._rotation % 360)
        if angle == 0:
            return
        if abs(angle) % 180 == 0:
            new_w, new_h = self.width, self.height
        else:
            new_w, new_h = self.height, self.width

        self._apply_activity_orientation(new_w, new_h)
        self._rebind_logical_texture(new_w, new_h)
        self._mark_orient_settle()
