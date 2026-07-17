# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.pgdisplay
"""

import pygame as pg

from displaysys import (
    DisplayDriver,
    color_rgb,
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


def _convert(e):
    """Convert a pygame event to an eventsys namedtuple."""
    t = e.type
    if t == pg.QUIT:
        return events.Quit(events.QUIT)
    if t == pg.MOUSEMOTION:
        return events.Motion(
            t,
            e.pos,
            e.rel,
            e.buttons,
            bool(getattr(e, "touch", False)),
            getattr(e, "window", None),
        )
    if t in (pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP):
        return events.Button(
            t,
            e.pos,
            e.button,
            bool(getattr(e, "touch", False)),
            getattr(e, "window", None),
        )
    if t == pg.MOUSEWHEEL:
        return events.Wheel(
            t,
            bool(getattr(e, "flipped", False)),
            getattr(e, "x", 0),
            getattr(e, "y", 0),
            getattr(e, "precise_x", getattr(e, "x", 0)),
            getattr(e, "precise_y", getattr(e, "y", 0)),
            bool(getattr(e, "touch", False)),
            getattr(e, "window", None),
        )
    if t in (pg.KEYDOWN, pg.KEYUP):
        return events.Key(t, _pg_key_name(e.key), e.key, e.mod, getattr(e, "scancode", 0), None)
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


def poll_event():
    """Non-blocking poll; return one eventsys event or ``None`` (not for QUEUE ``read``)."""
    e = pg.event.poll()
    if e.type == pg.NOEVENT:
        return None
    if e.type in events.filter:
        return _convert(e)
    return None


def get_events():
    """Drain the pygame queue; return a list of eventsys events or ``None``."""
    raw = pg.event.get()
    if not raw:
        return None
    eventlist = [_convert(e) for e in raw if e.type in events.filter]
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
    needs_refresh = True

    """
    A class to emulate an LCD using pygame.
    Provides scrolling and rotation functions similar to an LCD.  The .texture
    object functions as the LCD's internal memory.

    Args:
        width (int, optional): The width of the display. Defaults to 320.
        height (int, optional): The height of the display. Defaults to 240.
        rotation (int, optional): The rotation of the display. Defaults to 0.
        color_depth (int, optional): The color depth of the display. Defaults to 16.
        title (str, optional): The title of the display window. Defaults to "displaysys".
        scale (float, optional): The scale of the display. Defaults to 1.0.
        window_flags (int, optional): The flags for creating the display window. Defaults to pg.SHOWN

    Attributes:
        color_depth (int): The color depth of the display.
        touch_scale (float): The touch scale of the display.
    """

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
        self._render_dirty = False
        self._show_pending = False
        self._requires_byteswap = False
        self._frame_recorder = None

        self._bytes_per_pixel = color_depth // 8

        if self._scale != 1 and not hasattr(pg.transform, "scale_by"):
            if not quiet:
                print(
                    f"PGDisplay:  Scaling is set to {self._scale}, but pygame {pg.ver} does not support it."
                )
            self._scale = 1

        pg.init()
        try:
            info = pg.display.Info()
            desktop_w, desktop_h = info.current_w, info.current_h
        except Exception:
            desktop_w, desktop_h = 0, 0
        requested_scale = self._scale
        fitted = fit_scale_to_desktop(
            self.width, self.height, requested_scale, desktop_w, desktop_h
        )
        notify_board_config_scale_override("PGDisplay", requested_scale, fitted, quiet=quiet)
        if fitted != requested_scale:
            self._scale = fitted
            self.touch_scale = fitted
        _init_joysticks()

        self._buffer = pg.Surface(size=(self._width, self._height), depth=self.color_depth)
        self._buffer.fill((0, 0, 0))

        super().__init__(quiet=quiet)

    ############### Required API Methods ################

    def _lock_window_size(self) -> None:
        """Keep the OS window fixed to the scaled panel size (not user-resizable).

        Not passing ``pg.RESIZABLE`` already prevents a resize grip, but this
        also clamps the SDL window when a caller opts into ``pg.RESIZABLE`` or
        the platform WM would otherwise allow resizing.
        """
        try:
            from pygame._sdl2.video import Window
        except ImportError:
            return
        try:
            win = Window.from_display_module()
        except Exception:
            return
        win.resizable = False

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """
        self._window = pg.display.set_mode(
            size=(int(self.width * self._scale), int(self.height * self._scale)),
            flags=self._window_flags,
            depth=self.color_depth,
            display=0,
            vsync=0,
        )
        pg.display.set_caption(self._title)
        self._lock_window_size()

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
        """True while pygame-ce video is initialized and this driver is live."""
        if getattr(self, "_deinitialized", False):
            return False
        try:
            return bool(pg.get_init()) and bool(pg.display.get_init())
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
            pg.display.flip()
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
        """Release pygame resources."""
        self.close_frame_recorder()
        global _joysticks
        try:
            pg.joystick.quit()
        except Exception:
            pass
        _joysticks = []
        pg.display.quit()
        pg.quit()
