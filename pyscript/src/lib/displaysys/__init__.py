# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys — shared display core for *Python.

Each backend is a separate submodule; import only what your target needs::

    from displaysys import DisplayDriver, color565, capabilities
    from displaysys.busdisplay import BusDisplay
"""

import gc
import sys

try:
    from byteswap import byteswap as _byteswap_native

    byteswap = _byteswap_native
    _BYTESWAP_BACKEND = "native"
except ImportError:

    def byteswap(buf):
        """Swap 16-bit pixel bytes in place (portable fallback)."""
        n = len(buf) & ~1
        for i in range(0, n, 2):
            b0 = buf[i]
            buf[i] = buf[i + 1]
            buf[i + 1] = b0

    _BYTESWAP_BACKEND = "pure_python"

__all__ = [
    "DisplayDriver",
    "FFmpegFrameRecorder",
    "alloc_buffer",
    "byteswap",
    "capabilities",
    "color332",
    "color565",
    "color565_swapped",
    "color_rgb",
    "default_quit_chord",
]

_DEFAULT_AUTO_REFRESH_PERIOD = 33
_DESKTOP_SCALE_MARGIN = 48


def fit_scale_to_desktop(
    width, height, scale, desktop_w, desktop_h, *, margin=_DESKTOP_SCALE_MARGIN
):
    """Return the largest scale <= *scale* so the window fits on the desktop."""
    if scale <= 0 or desktop_w <= 0 or desktop_h <= 0:
        return 1.0 if scale <= 0 else scale
    max_w = desktop_w - margin
    max_h = desktop_h - margin
    if max_w <= 0 or max_h <= 0:
        return scale
    fit = min(max_w / width, max_h / height)
    if fit < scale:
        return fit
    return scale


def notify_board_config_scale_override(driver_name, requested, fitted, *, quiet=False):
    """Tell the user when a desktop driver reduces board_config scale to fit the screen."""
    if quiet or fitted == requested:
        return
    print(
        f"{driver_name}: overriding board_config scale {requested} -> {fitted:.2f} to fit desktop"
    )


def capabilities():
    """Static metadata for the modular displaysys install model (no backend imports)."""
    return {
        "dialect": sys.implementation.name,
        "byteswap": _BYTESWAP_BACKEND,
        "modules": {
            "busdisplay": {"eventsys": False, "auto_refresh": False},
            "fbdisplay": {"eventsys": False, "auto_refresh": False},
            "pixeldisplay": {"eventsys": False, "auto_refresh": False},
            "epaperdisplay": {
                "eventsys": False,
                "auto_refresh": False,
                "buffer_push": "displayio_or_bus",
            },
            "sdldisplay": {
                "eventsys": True,
                "auto_refresh": True,
                "default_period_ms": _DEFAULT_AUTO_REFRESH_PERIOD,
                "async_default": False,
                "touch_scale": "1.0 (logical renderer size)",
                "scroll_emulation": True,
            },
            "pgdisplay": {
                "eventsys": True,
                "auto_refresh": True,
                "default_period_ms": _DEFAULT_AUTO_REFRESH_PERIOD,
                "async_default": False,
                "touch_scale": "window scale",
                "scroll_emulation": True,
            },
            "psdisplay": {
                "eventsys": True,
                "auto_refresh": True,
                "default_period_ms": _DEFAULT_AUTO_REFRESH_PERIOD,
                "async_default": True,
                "touch_scale": "canvas layout scale",
                "scroll_emulation": True,
            },
            "jndisplay": {
                "eventsys": True,
                "auto_refresh": True,
                "default_period_ms": _DEFAULT_AUTO_REFRESH_PERIOD,
                "async_default": True,
                "touch_scale": "1.0",
                "scroll_emulation": True,
            },
        },
    }


def default_quit_chord():
    """Default CTRL+Q quit chord for event-backend displays (lazy-imports eventsys.keys)."""
    from eventsys.keys import Keys

    return (Keys.K_q, Keys.KMOD_CTRL)


def alloc_buffer(size):
    """
    Create a new buffer of the specified size.  In the future, this function may be
    modified to use port-specific memory allocation such as ESP32's heap_caps_malloc.

    Args:
        size (int): The size of the buffer to create.

    Returns:
        (memoryview): The new buffer.
    """
    return memoryview(bytearray(size))


def color565(r, g=None, b=None):
    """
    Convert RGB values to a 16-bit color value.

    Args:
        r (int, tuple or list): The red value or a tuple or list of RGB values.
        g (int): The green value.
        b (int): The blue value.

    Returns:
        (int): The 16-bit color value
    """
    if isinstance(r, (tuple, list)):
        r, g, b = r[:3]
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def color565_swapped(r, g=0, b=0):
    """
    Convert RGB to 16-bit RGB565 with byte order swapped for some displays.

    Args:
        r (int | tuple | list): Red value, or an (r, g, b) sequence.
        g (int): Green value when r is an int.
        b (int): Blue value when r is an int.

    Returns:
        int: Byte-swapped RGB565 color.
    """
    if isinstance(r, (tuple, list)):
        r, g, b = r[:3]
    color = color565(r, g, b)
    return (color & 0xFF) << 8 | (color & 0xFF00) >> 8


def color332(r, g, b):
    """
    Convert RGB to 8-bit RGB332 color.

    Args:
        r (int): Red (0-255).
        g (int): Green (0-255).
        b (int): Blue (0-255).

    Returns:
        int: RGB332 color byte.
    """
    return (r & 0xE0) | ((g >> 3) & 0x1C) | (b >> 6)


def color_rgb(color):
    """
    Expand a display color to an (r, g, b) tuple.

    Args:
        color (int | tuple | list | bytearray): 16-bit RGB565 int or 2-3 byte sequence.

    Returns:
        tuple[int, int, int]: Red, green, blue (0-255 each).
    """
    if isinstance(color, int):
        # convert 16-bit int color to 2 bytes
        color = (color & 0xFF, color >> 8)
    if len(color) == 2:
        r = color[1] & 0xF8 | (color[1] >> 5) & 0x7  # 5 bit to 8 bit red
        g = color[1] << 5 & 0xE0 | (color[0] >> 3) & 0x1F  # 6 bit to 8 bit green
        b = color[0] << 3 & 0xF8 | (color[0] >> 2) & 0x7  # 5 bit to 8 bit blue
    else:
        r, g, b = color
    return (r, g, b)


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


class DisplayDriver:
    """
    Base class for all display backends (BusDisplay, SDLDisplay, PGDisplay, FBDisplay, etc.).

    Subclasses implement drawing (``blit_rect``, ``fill_rect``, ``pixel``),
    presentation (``show()``), and teardown (``quit()`` / ``deinit()``). Most
    applications use a concrete driver from ``board_config.display`` rather than
    instantiating this class directly.

    Periodic presentation when needed is driven by ``eventsys.Runtime`` (see
    ``needs_refresh``).
    """

    needs_refresh = False

    def __init__(self):
        if not hasattr(self, "_quiet"):
            self._quiet = False
        if not self._quiet:
            print(f"Initializing {self.__class__.__name__}...")
        gc.collect()

        self.byteswap = byteswap
        self.touch_scale = 1.0
        self._vssa = False  # False means no vertical scroll
        self._auto_byteswap = self.requires_byteswap
        self._touch_device = None
        self._frame_recorder = None
        self.init()
        gc.collect()
        self._deinitialized = False
        if not self._quiet:
            print(f"{self.__class__.__name__}: initialized.")
            if self.requires_byteswap:
                print(f"{self.__class__.__name__}: requires_byteswap = True")

    def __del__(self):
        self.deinit()

    ############### Universal API Methods, not usually overridden ################

    @property
    def width(self) -> int:
        """The width of the display in pixels."""
        if ((self._rotation // 90) & 0x1) == 0x1:  # if rotation index is odd
            return self._height
        return self._width

    @property
    def height(self) -> int:
        """The height of the display in pixels."""
        if ((self._rotation // 90) & 0x1) == 0x1:  # if rotation index is odd
            return self._width
        return self._height

    @property
    def rotation(self) -> int:
        """
        The rotation of the display.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, value) -> None:
        """
        Sets the rotation of the display.

        Args:
            value (int): The rotation of the display in degrees.
        """

        if value % 90 != 0:
            value = value * 90

        if value == self._rotation:
            return

        if not self._quiet:
            print(f"{self.__class__.__name__}.rotation():  Setting rotation to {value}")
        self._rotation_helper(value)
        if not self._quiet:
            print("done setting rotation")

        self._rotation = value

        if self._touch_device is not None:
            self._touch_device.rotation = value

        self.init()

    @property
    def touch_device(self) -> object:
        """
        The touch device.
        """
        return self._touch_device

    @touch_device.setter
    def touch_device(self, value) -> None:
        """
        Sets the touch device.

        Args:
            value (object): The touch device.
        """
        if hasattr(value, "rotation") or value is None:
            self._touch_device = value
        else:
            raise ValueError("touch_device must have a rotation attribute")
        self._touch_device.rotation = self.rotation

    def fill(self, color):
        """
        Fill the display with a color.

        Args:
            color (int): The color to fill the display with.
        """
        return self.fill_rect(0, 0, self.width, self.height, color)

    def scroll(self, dx, dy) -> None:
        """
        Scroll the display.

        Args:
            dx (int): The number of pixels to scroll horizontally.
            dy (int): The number of pixels to scroll vertically.
        """
        if dy != 0:
            if self._vssa is not None:
                self.vscsad(self._vssa + dy)
            else:
                self.vscsad(dy)
        if dx != 0:
            raise NotImplementedError("Horizontal scrolling not supported")

    def disable_auto_byteswap(self, value: bool) -> bool:
        """
        Disable byte swapping in the display driver.

        If self.requires_byteswap and the guest application is capable of byte swapping color data
        check to see if byte swapping can be disabled.  If so, disable it.

        Usage:
            ```
            # If byte swapping is required and the display driver is capable of having byte swapping disabled,
            # disable it and set a flag so we can swap the color bytes as they are created.
            if display_drv.requires_byteswap:
                needs_swap = display_drv.disable_auto_byteswap(True)
            else:
                needs_swap = False
            ```

        Args:
            value (bool): Whether to disable byte swapping.

        Returns:
            (bool): Whether byte swapping was disabled successfully.

        """
        if self._requires_byteswap:
            self._auto_byteswap = not value
        else:
            self._auto_byteswap = False
        if not self._quiet:
            print(f"{self.__class__.__name__}:  auto byte swapping = {self._auto_byteswap}")
        return not self._auto_byteswap

    @property
    def requires_byteswap(self) -> bool:
        """
        Whether the display requires byte swapping.
        """
        return self._requires_byteswap

    def blit_transparent(self, buf: memoryview, x: int, y: int, w: int, h: int, key: int):
        """
        Blit a buffer with transparency.

        Args:
            buf (memoryview): The buffer to blit.
            x (int): The x coordinate to blit to.
            y (int): The y coordinate to blit to.
            w (int): The width to blit.
            h (int): The height to blit.
            key (int): The color key to use for transparency.

        Returns:
            (tuple): The x, y, w, h coordinates of the blitted area.
        """
        BPP = self.color_depth // 8
        key_bytes = key.to_bytes(BPP, "little")
        stride = w * BPP
        for j in range(h):
            rowstart = j * stride
            colstart = 0
            # iterate over each pixel looking for the first non-key pixel
            while colstart < stride:
                startoffset = rowstart + colstart
                if buf[startoffset : startoffset + BPP] != key_bytes:
                    # found a non-key pixel
                    # then iterate over each pixel looking for the next key pixel
                    colend = colstart
                    while colend < stride:
                        endoffset = rowstart + colend
                        if buf[endoffset : endoffset + BPP] == key_bytes:
                            break
                        colend += BPP
                    # blit the non-key pixels
                    self.blit_rect(
                        buf[rowstart + colstart : rowstart + colend],
                        x + colstart // BPP,
                        y + j,
                        (colend - colstart) // BPP,
                        1,
                    )
                    colstart = colend
                else:
                    colstart += BPP
        return (x, y, w, h)

    @property
    def vscroll(self) -> int:
        """
        The vertical scroll position relative to the top fixed area.

        Returns:
            (int): The vertical scroll position.
        """
        return self.vscsad() - self._tfa

    @vscroll.setter
    def vscroll(self, y) -> None:
        """
        Set the vertical scroll position relative to the top fixed area.

        Args:
            y (int): The vertical scroll position.
        """
        self.vscsad((y % self._vsa) + self._tfa)

    def set_vscroll(self, tfa=0, bfa=0) -> None:
        """
        Set the vertical scroll definition and move the vertical scroll to the top.

        Args:
            tfa (int): The top fixed area.
            bfa (int): The bottom fixed area.
        """
        self.vscrdef(tfa, self.height - tfa - bfa, bfa)
        self.vscroll = 0

    @property
    def tfa(self) -> int:
        """
        The top fixed area set by set_vscroll or vscrdef.

        Returns:
            (int): The top fixed area.
        """
        return self._tfa

    @property
    def vsa(self) -> int:
        """
        The vertical scroll area set by set_vscroll or vscrdef.

        Returns:
            (int): The vertical scroll area.
        """
        return self._vsa

    @property
    def bfa(self) -> int:
        """
        The bottom fixed area set by set_vscroll or vscrdef.

        Returns:
            (int): The bottom fixed area.
        """
        return self._bfa

    def translate_point(self, point) -> tuple:
        """
        Translate a point from real coordinates to scrolled coordinates.

        Useful for touch events.

        Args:
            point (tuple): The x and y coordinates to translate.

        Returns:
            (tuple): The translated x and y coordinates.
        """
        x, y = point
        if self.vscsad() and self.tfa < y < self.height - self.bfa:
            y = y + self.vscsad() - self.tfa
            if y >= (self.vsa + self.tfa):
                y %= self.vsa
        return x, y

    def scroll_by(self, value):
        self.vscroll += value

    def scroll_to(self, value):
        self.vscroll = value

    @property
    def tfa_area(self):
        """
        Top fixed area for vertical scrolling.

        Returns:
            tuple[int, int, int, int]: ``(x, y, width, height)`` of the top fixed band.
        """
        return (0, 0, self.width, self.tfa)

    @property
    def vsa_area(self):
        """
        The vertical scroll area as an Area object.

        Returns:
            (tuple): The vertical scroll area.
        """
        return (0, self.tfa, self.width, self.vsa)

    @property
    def bfa_area(self):
        """
        The bottom fixed area as an Area object.

        Returns:
            (tuple): The bottom fixed area.
        """
        return (0, self.tfa + self.vsa, self.width, self.bfa)

    ############### Common API Methods, sometimes overridden ################

    def vscrdef(self, tfa: int, vsa: int, bfa: int) -> None:
        """
        Set the vertical scroll definition.  Should be overridden by the
        subclass and called as super().vscrdef(tfa, vsa, bfa).

        Args:
            tfa (int): The top fixed area.
            vsa (int): The vertical scroll area.
            bfa (int): The bottom fixed area.
        """
        if tfa + vsa + bfa != self.height:
            raise ValueError("Sum of top, scroll and bottom areas must equal screen height")
        self._tfa = tfa
        self._vsa = vsa
        self._bfa = bfa

    def vscsad(self, vssa: int | None = None) -> int:
        """
        Set or get the vertical scroll start address.  Should be overridden by the
        subclass and called as super().vscsad(y).

        Args:
            vssa (int): The vertical scroll start address.

        Returns:
            (int): The vertical scroll start address.
        """
        if vssa is not None:
            while vssa < 0:
                vssa += self._height
            if vssa >= self._height:
                vssa %= self._height
            self._vssa = vssa
        return vssa

    def _rotation_helper(self, value):
        """
        Helper function to set the rotation of the display.

        Args:
            value (int): The rotation of the display in degrees.
        """
        # override this method in subclasses to handle rotation

    ############### Empty API Methods, must be overridden if applicable ################

    @property
    def power(self) -> bool:
        """The power state of the display."""
        return -1

    @power.setter
    def power(self, value: bool) -> None:
        """
        Set the power state of the display.  Should be overridden by the subclass.

        Args:
            value (bool): True to power on, False to power off.
        """
        return

    @property
    def brightness(self) -> float:
        """The brightness of the display."""
        return -1

    @brightness.setter
    def brightness(self, value: float) -> None:
        """
        Set the brightness of the display.  Should be overridden by the subclass.

        Args:
            value (int, float): The brightness value from 0 to 1.
        """
        return

    def invert_colors(self, value: bool) -> None:
        """
        Invert the colors of the display.  Should be overridden by the subclass.

        Args:
            value (bool): True to invert the colors, False to restore the colors.
        """
        return

    def reset(self) -> None:
        """
        Perform a reset of the display.  Should be overridden by the subclass.
        """
        return

    def hard_reset(self) -> None:
        """
        Perform a hardware reset of the display.  Should be overridden by the subclass.
        """
        return

    def soft_reset(self) -> None:
        """
        Perform a software reset of the display.  Should be overridden by the subclass.
        """
        return

    def sleep_mode(self, value: bool) -> None:
        """
        Set the sleep mode of the display.  Should be overridden by the subclass.

        Args:
            value (bool): True to enter sleep mode, False to exit sleep mode.
        """
        return

    @property
    def frame_recording(self) -> bool:
        """True while a frame recorder is attached (PGDisplay only today)."""
        return self._frame_recorder is not None

    def open_frame_recorder(self, path, *, fps=12, width=None, height=None):
        """
        Attach an ffmpeg-backed recorder that receives one RGB24 frame per ``show()``.

        Only PGDisplay implements this today; other backends raise
        ``NotImplementedError``.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support frame recording")

    def open_frame_recorder_from_env(
        self, env_var="PYDISPLAY_VIDEO", fps_env="PYDISPLAY_VIDEO_FPS"
    ):
        """Open a recorder when ``env_var`` points at an output ``.mp4`` path."""
        import os

        path = os.environ.get(env_var, "").strip()
        if not path:
            return None
        fps = int(os.environ.get(fps_env, "12"))
        return self.open_frame_recorder(path, fps=fps)

    def close_frame_recorder(self):
        """Finalize and detach any active frame recorder."""
        recorder = self._frame_recorder
        self._frame_recorder = None
        if recorder is not None:
            recorder.close()

    def _record_frame(self, rgb_bytes) -> None:
        """Deliver one presented RGB24 frame to the active recorder, if any."""
        if self._frame_recorder is not None:
            self._frame_recorder.write(rgb_bytes)

    def deinit(self) -> None:
        """
        Run subclass cleanup. Idempotent.

        The broker owns the shared refresh timer, so there is no display-owned
        timer to stop here; ``board_config`` stops the timer on quit via
        ``runtime.stop_timer``.
        """
        if getattr(self, "_deinitialized", False):
            return
        self._deinitialized = True
        self.close_frame_recorder()
        self._deinit()

    def _deinit(self) -> None:
        """Subclass resource cleanup hook, called after the timer is stopped."""
        return

    def quit(self, code: int = 0, force: bool = False) -> None:
        """Release display resources (REPL-safe unless ``force=True``). Called on QUIT."""
        self.deinit()
        if force:
            raise SystemExit(code)

    def force_quit(self, code: int = 0) -> None:
        """Release resources then exit the process (alias for ``quit(code, force=True)``)."""
        self.quit(code, force=True)

    def show(self, *args, **kwargs) -> None:
        """
        Show the display.  Base class method does nothing.  May be overridden by subclasses.
        """
        return
