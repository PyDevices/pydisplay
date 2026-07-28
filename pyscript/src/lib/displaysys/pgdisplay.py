# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.pgdisplay
"""

import pygame as pg

from displaysys import (
    _DESKTOP_WINDOW_CHROME_H,
    _DESKTOP_WINDOW_CHROME_W,
    DisplayDriver,
    color_rgb,
    desktop_work_area,
    fit_scale_to_desktop,
    notify_board_config_scale_override,
)
from eventsys import events
from eventsys.keys import default_quit_chord

__all__ = ["FFmpegFrameRecorder", "PGDisplay", "get_events", "poll_event"]


class FFmpegFrameRecorder:
    """Pipe fixed-size RGB24 frames to ffmpeg for MP4 output."""

    __slots__ = ("_closed", "_frame_bytes", "_frames", "_proc", "fps", "height", "path", "width")

    def __init__(self, path, width, height, fps=12):
        import subprocess

        self.path = path
        self.width = width
        self.height = height
        self.fps = fps
        self._frames = 0
        self._closed = False
        self._frame_bytes = width * height * 3
        self._proc = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s",
                f"{width}x{height}",
                "-r",
                str(fps),
                "-i",
                "pipe:0",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                path,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def write(self, rgb_bytes):
        if self._closed:
            return
        if len(rgb_bytes) != self._frame_bytes:
            raise ValueError(
                f"frame size {len(rgb_bytes)} != expected {self._frame_bytes} "
                f"for {self.width}x{self.height} RGB24"
            )
        self._proc.stdin.write(rgb_bytes)
        self._frames += 1

    def close(self):
        if self._closed:
            return self._frames
        self._closed = True
        try:
            self._proc.stdin.close()
        except Exception:
            pass
        err = self._proc.stderr.read().decode("utf-8", errors="replace")
        try:
            self._proc.stderr.close()
        except Exception:
            pass
        rc = self._proc.wait()
        if rc != 0:
            tail = "\n".join(err.strip().splitlines()[-8:])
            raise RuntimeError(f"ffmpeg exited {rc} for {self.path}:\n{tail}")
        return self._frames


def _pg_key_name(key):
    try:
        return pg.key.name(key)
    except Exception:
        return str(key)


_pg_displays = []


def _pg_window_cls():
    """Return public ``pygame.Window`` (pygame-ce) with software ``get_surface``/``flip``.

    Does **not** use ``pygame._sdl2.*``. Raises ``ImportError`` when the
    interpreter only has classic pygame (so ``board_config`` can fall back to SDL).
    """
    Window = getattr(pg, "Window", None)
    if Window is None or not hasattr(Window, "get_surface") or not hasattr(Window, "flip"):
        raise ImportError(
            "PGDisplay requires pygame-ce with public pygame.Window "
            "(get_surface/flip); classic pygame / pygame._sdl2 is not supported"
        )
    return Window


# Fail at import time (not only in PGDisplay.__init__) so board_config's
# try/except ImportError selects SDL when pygame-ce is absent.
_pg_window_cls()


def _window_id_of(window):
    if window is None:
        return None
    return getattr(window, "id", window)


def _display_for_window(window):
    wid = _window_id_of(window)
    if wid is None:
        return None
    for display in _pg_displays:
        if getattr(display, "_window_id", None) == wid:
            return display
    return None


def _panel_size(window=None):
    """Logical panel size for normalizing pygame finger coords (0..1 → pixels)."""
    d = _display_for_window(window)
    if d is None and _pg_displays:
        d = _pg_displays[0]
    if d is not None:
        return int(d.width), int(d.height)
    return 320, 240


def _handle_window_close(window):
    display = _display_for_window(window)
    if display is None or display is _pg_displays[0] or len(_pg_displays) <= 1:
        return events.Quit(events.QUIT)
    runtime = getattr(display, "runtime", None)
    if runtime is not None and callable(getattr(runtime, "remove_display", None)):
        runtime.remove_display(display)
    else:
        try:
            display.quit()
        except Exception:
            pass
        try:
            _pg_displays.remove(display)
        except ValueError:
            pass
    return None


def _convert(e):
    """Convert a pygame event to an eventsys namedtuple."""
    t = e.type
    if t == pg.QUIT:
        return events.Quit(events.QUIT)
    if t == getattr(pg, "WINDOWCLOSE", -1):
        return _handle_window_close(getattr(e, "window", None))
    win = _window_id_of(getattr(e, "window", None))
    if t == pg.MOUSEMOTION:
        return events.Motion(
            t,
            e.pos,
            e.rel,
            e.buttons,
            bool(getattr(e, "touch", False)),
            win,
        )
    if t in (pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP):
        return events.Button(
            t,
            e.pos,
            e.button,
            bool(getattr(e, "touch", False)),
            win,
        )
    if t in (pg.FINGERDOWN, pg.FINGERUP, pg.FINGERMOTION):
        # Real OS multitouch (touchscreen). Same contract as sdldisplay SDL_FINGER*.
        # Not mouse-chord inject — trackpad OS-pinch still will not appear here.
        w, h = _panel_size(getattr(e, "window", None))
        fx = float(getattr(e, "x", 0.0))
        fy = float(getattr(e, "y", 0.0))
        fid = int(getattr(e, "finger_id", getattr(e, "finger", 0)))
        return events.Finger(t, (int(fx * w), int(fy * h)), fid, win)
    if t == pg.MOUSEWHEEL:
        return events.Wheel(
            t,
            bool(getattr(e, "flipped", False)),
            getattr(e, "x", 0),
            getattr(e, "y", 0),
            getattr(e, "precise_x", getattr(e, "x", 0)),
            getattr(e, "precise_y", getattr(e, "y", 0)),
            bool(getattr(e, "touch", False)),
            win,
        )
    if t in (pg.KEYDOWN, pg.KEYUP):
        return events.Key(t, _pg_key_name(e.key), e.key, e.mod, getattr(e, "scancode", 0), win)
    if t == pg.JOYAXISMOTION:
        return events.JoyAxisMotion(t, e.instance_id, e.axis, e.value / 32767.0)
    if t == pg.JOYBALLMOTION:
        return events.JoyBallMotion(t, e.instance_id, e.ball, e.rel)
    if t == pg.JOYHATMOTION:
        return events.JoyHatMotion(t, e.instance_id, e.hat, e.value)
    if t == pg.JOYBUTTONDOWN:
        return events.JoyButtonDown(t, e.instance_id, e.button)
    if t == pg.JOYBUTTONUP:
        return events.JoyButtonUp(t, e.instance_id, e.button)
    return events.Unknown(t)


def _process_pg_event(e):
    if e.type == pg.NOEVENT:
        return None
    if e.type == getattr(pg, "WINDOWCLOSE", -1) or e.type in events.filter:
        return _convert(e)
    return None


def poll_event():
    """Non-blocking poll; return one eventsys event or ``None`` (not for QUEUE ``read``)."""
    return _process_pg_event(pg.event.poll())


def get_events():
    """Drain the pygame queue; return a list of eventsys events or ``None``."""
    raw = pg.event.get()
    if not raw:
        return None
    eventlist = []
    for e in raw:
        evt = _process_pg_event(e)
        if evt is not None:
            eventlist.append(evt)
    return eventlist if eventlist else None


# Opened joystick handles, kept referenced so PyGame keeps delivering their
# events.  PyGame's joystick events (JOYAXISMOTION, JOYBUTTONDOWN, ...) already
# share eventsys's numeric types and attribute names, so they flow through
# share eventsys's numeric types once joysticks are opened.
_joysticks = []


def _init_joysticks() -> None:
    """
    Initialize the joystick subsystem and open all connected joysticks.

    Joysticks must be opened for PyGame to deliver their events.  Devices
    connected after startup are not hot-plugged (connect controllers before
    launching).  Failures are ignored so a missing joystick subsystem never
    breaks the display.
    """
    try:
        pg.joystick.init()
        for i in range(pg.joystick.get_count()):
            js = pg.joystick.Joystick(i)
            js.init()
            _joysticks.append(js)
    except Exception:
        pass


class PGDisplay(DisplayDriver):
    """Emulate an LCD window with pygame-ce (``pygame.Window``).

    Requires pygame-ce with public ``Window.get_surface`` / ``Window.flip``
    (no ``pygame._sdl2``). Provides scrolling and rotation similar to a panel
    driver; scale is reduced when the window would not fit the desktop work area.

    Args:
        width (int, optional): Panel width in pixels. Defaults to 320.
        height (int, optional): Panel height in pixels. Defaults to 240.
        rotation (int, optional): Rotation in degrees. Defaults to 0.
        color_depth (int, optional): Bits per pixel. Defaults to 16.
        title (str, optional): Window title. Defaults to ``"displaysys"``.
        scale (float, optional): Window scale factor. Defaults to 1.0.
        window_flags (int, optional): pygame display flags. Defaults to ``pg.SHOWN``.
        quiet (bool): Suppress init chatter when True.

    Attributes:
        color_depth (int): Bits per pixel.
        touch_scale (float): Scale used to map host pointer coords into panel space.
        needs_refresh (bool): True — ``eventsys.Runtime`` drives periodic ``show()``.
    """

    needs_refresh = True

    def __init__(
        self,
        width=320,
        height=240,
        rotation=0,
        color_depth=16,
        title="displaysys",
        scale=1.0,
        window_flags=pg.SHOWN,
        *,
        quiet=False,
    ):
        self._width = width
        self._height = height
        self._rotation = rotation
        self.color_depth = color_depth
        self._title = title
        self._window_flags = window_flags
        self._scale = scale
        self.touch_scale = scale
        self.quit_chord = default_quit_chord()
        self._buffer = None
        self._pg_window = None
        self._window_id = None
        self._window = None  # Window.get_surface() display surface
        self.runtime = None
        self._render_dirty = False
        self._show_pending = False
        self._requires_byteswap = False
        self._frame_recorder = None

        self._bytes_per_pixel = color_depth // 8

        # Fail early if this interpreter lacks pygame-ce Window (e.g. system python3).
        _pg_window_cls()

        if self._scale != 1 and not hasattr(pg.transform, "scale_by"):
            if not quiet:
                print(
                    f"PGDisplay:  Scaling is set to {self._scale}, but pygame {pg.ver} does not support it."
                )
            self._scale = 1

        pg.init()
        ux, uy, desktop_w, desktop_h = desktop_work_area()
        if desktop_w <= 0 or desktop_h <= 0:
            try:
                info = pg.display.Info()
                desktop_w, desktop_h = info.current_w, info.current_h
                ux, uy = 0, 0
            except Exception:
                desktop_w, desktop_h = 0, 0
        self._work_area = (ux, uy, desktop_w, desktop_h)
        requested_scale = self._scale
        fitted = fit_scale_to_desktop(
            self.width,
            self.height,
            requested_scale,
            desktop_w,
            desktop_h,
            chrome_w=_DESKTOP_WINDOW_CHROME_W,
            chrome_h=_DESKTOP_WINDOW_CHROME_H,
        )
        notify_board_config_scale_override("PGDisplay", requested_scale, fitted, quiet=quiet)
        if fitted != requested_scale:
            self._scale = fitted
            self.touch_scale = fitted
        _init_joysticks()

        self._buffer = pg.Surface(size=(self._width, self._height), depth=self.color_depth)
        self._buffer.fill((0, 0, 0))

        super().__init__(quiet=quiet)
        # DisplayDriver.__init__ used to reset touch_scale to 1.0; keep window scale
        # so HostEventsDevice maps pygame coords into panel space.
        self.touch_scale = self._scale
        if self not in _pg_displays:
            _pg_displays.append(self)

    ############### Required API Methods ################

    def _lock_window_size(self) -> None:
        """Keep the OS window fixed to the scaled panel size (not user-resizable)."""
        win = self._pg_window
        if win is not None:
            try:
                win.resizable = False
            except Exception:
                pass

    def _place_window(self, win_w, win_h) -> None:
        """Center the window in the usable work area (taskbar / chrome aware)."""
        win = self._pg_window
        if win is None:
            return
        ux, uy, uw, uh = getattr(self, "_work_area", (0, 0, 0, 0))
        if uw <= 0 or uh <= 0:
            return
        x = ux + max(0, (uw - win_w) // 2)
        y = uy + _DESKTOP_WINDOW_CHROME_H + max(0, (uh - _DESKTOP_WINDOW_CHROME_H - win_h) // 2)
        try:
            win.position = (x, y)
        except Exception:
            pass

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """
        win_w = int(self.width * self._scale)
        win_h = int(self.height * self._scale)
        Window = _pg_window_cls()
        if self._pg_window is None:
            self._pg_window = Window(title=self._title, size=(win_w, win_h))
            self._window_id = int(self._pg_window.id)
        else:
            try:
                self._pg_window.size = (win_w, win_h)
                self._pg_window.title = self._title
            except Exception:
                pass
        self._window = self._pg_window.get_surface()
        self._lock_window_size()
        self._place_window(win_w, win_h)

        super().vscrdef(
            0, self.height, 0
        )  # Set the vertical scroll definition without calling show
        self.vscsad(False)  # Scroll offset; set to False to disable scrolling

    def blit_rect(self, buffer: memoryview, x: int, y: int, w: int, h: int):
        """
        Blit a buffer into the logical framebuffer.  Compositing is deferred until ``show()``.
        """

        for i in range(h):
            for j in range(w):
                pixel_index = (i * w + j) * self._bytes_per_pixel
                color = color_rgb(buffer[pixel_index : pixel_index + self._bytes_per_pixel])
                self._buffer.set_at((x + j, y + i), color)
        self._render_dirty = True
        return (x, y, w, h)

    def fill_rect(self, x: int, y: int, w: int, h: int, c: int):
        """
        Fill a rectangle in the logical framebuffer.  Compositing is deferred until ``show()``.
        """
        fillRect = pg.Rect(x, y, w, h)
        self._buffer.fill(color_rgb(c), fillRect)
        self._render_dirty = True
        return (x, y, w, h)

    def pixel(self, x: int, y: int, c: int):
        """
        Set a pixel on the display.

        Args:
            x (int): The x-coordinate of the pixel.
            y (int): The y-coordinate of the pixel.
            c (int): The color of the pixel.

        Returns:
            (tuple): A tuple containing the x, y, w & h values.
        """
        return self.blit_rect(bytearray(c.to_bytes(2, "little")), x, y, 1, 1)

    ############### API Method Overrides ################

    def vscrdef(self, tfa: int, vsa: int, bfa: int) -> None:
        """
        Set the vertical scroll definition.

        Args:
            tfa (int): The top fixed area.
            vsa (int): The vertical scroll area.
            bfa (int): The bottom fixed area.
        """
        super().vscrdef(tfa, vsa, bfa)
        self._render_dirty = True

    def vscsad(self, vssa=None) -> int:
        """
        Set the vertical scroll start address.

        Args:
            vssa (Optional[int], optional): The vertical scroll start address. Defaults to None.

        Returns:
            int: The vertical scroll start address.
        """
        if vssa is not None:
            super().vscsad(vssa)
            self._render_dirty = True
        return self._vssa

    def _rotation_helper(self, value):
        """
        Helper function for the rotation setter.
        """
        if (angle := (value % 360) - (self._rotation % 360)) != 0:
            tempBuffer = pg.transform.rotate(self._buffer, -angle)
            self._buffer = tempBuffer

    ############### Class Specific Methods ##############

    def _video_active(self) -> bool:
        """True while pygame is initialized and this window is live."""
        if getattr(self, "_deinitialized", False):
            return False
        if self._pg_window is None or self._window is None:
            return False
        try:
            return bool(pg.get_init())
        except pg.error:
            return False

    def _buffer_rgb(self) -> bytes:
        """Export the logical framebuffer as packed RGB24 bytes."""
        if hasattr(pg.image, "tostring"):
            return pg.image.tostring(self._buffer, "RGB")
        return pg.image.tobytes(self._buffer, "RGB")

    @property
    def frame_recording(self) -> bool:
        """True while an ffmpeg frame recorder is attached."""
        return self._frame_recorder is not None

    def open_frame_recorder(self, path, *, fps=12, width=None, height=None):
        """Attach an ffmpeg-backed recorder that receives one RGB24 frame per ``show()``."""
        self.close_frame_recorder()
        w = self.width if width is None else width
        h = self.height if height is None else height
        self._frame_recorder = FFmpegFrameRecorder(path, w, h, fps)
        return self._frame_recorder

    def close_frame_recorder(self):
        """Finalize and detach any active frame recorder."""
        recorder = self._frame_recorder
        self._frame_recorder = None
        if recorder is not None:
            recorder.close()

    def _record_frame(self, rgb_bytes) -> None:
        if self._frame_recorder is not None:
            self._frame_recorder.write(rgb_bytes)

    def render(self, renderRect=None) -> None:
        """
        Composite the logical framebuffer to the window.  Called from ``show()`` when draws are pending.
        """
        if not self._video_active():
            return
        s = self._scale
        buffer = pg.transform.scale_by(self._buffer, s) if s != 1 else self._buffer
        if not (y_start := self.vscsad()):
            if renderRect is not None:
                x, y, w, h = renderRect
                renderRect = pg.Rect(x * s, y * s, w * s, h * s)
                dest = renderRect
            else:
                dest = (0, 0)
            self._window.blit(buffer, dest, renderRect)
        else:
            # Ignore renderRect and render the entire buffer to the window in four steps
            y_start *= s
            tfa = self._tfa * s
            vsa = self._vsa * s
            bfa = self._bfa * s
            width = self.width * s

            if tfa > 0:
                tfaRect = pg.Rect(0, 0, width, tfa)
                self._window.blit(buffer, tfaRect, tfaRect)

            vsaTopHeight = vsa + tfa - y_start
            vsaTopSrcRect = pg.Rect(0, y_start, width, vsaTopHeight)
            vsaTopDestRect = pg.Rect(0, tfa, width, vsaTopHeight)
            self._window.blit(buffer, vsaTopDestRect, vsaTopSrcRect)

            vsaBtmHeight = vsa - vsaTopHeight
            vsaBtmSrcRect = pg.Rect(0, tfa, width, vsaBtmHeight)
            vsaBtmDestRect = pg.Rect(0, tfa + vsaTopHeight, width, vsaBtmHeight)
            self._window.blit(buffer, vsaBtmDestRect, vsaBtmSrcRect)

            if bfa > 0:
                bfaRect = pg.Rect(0, tfa + vsa, width, bfa)
                self._window.blit(buffer, bfaRect, bfaRect)

    def show(self, _timer=None) -> None:
        """
        Show the display.
        """
        if not self._video_active():
            return
        if self._render_dirty:
            self.render()
            self._render_dirty = False
        if self._frame_recorder is not None:
            self._record_frame(self._buffer_rgb())
        try:
            self._pg_window.flip()
        except pg.error:
            if getattr(self, "_deinitialized", False):
                return
            raise

    def quit(self, code: int = 0, force: bool = False) -> None:
        """Release pygame resources (REPL-safe unless ``force=True``)."""
        self.deinit()
        if not force:
            return
        try:
            import os

            os._exit(code)
        except Exception:
            pass
        raise SystemExit(code)

    def force_quit(self, code: int = 0) -> None:
        """Release pygame resources then hard-exit the process."""
        self.quit(code, force=True)

    def _deinit(self) -> None:
        """Release this window; quit pygame only when no PGDisplay remains."""
        self.close_frame_recorder()
        try:
            _pg_displays.remove(self)
        except ValueError:
            pass
        window = self._pg_window
        self._pg_window = None
        self._window = None
        self._window_id = None
        self.runtime = None
        if window is not None:
            try:
                window.destroy()
            except Exception:
                pass
        if _pg_displays:
            return
        global _joysticks
        try:
            pg.joystick.quit()
        except Exception:
            pass
        _joysticks = []
        try:
            pg.quit()
        except Exception:
            pass
        self._window = None
        self._buffer = None
