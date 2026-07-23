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
        n = len(buf)
        if n & 1:
            raise ValueError("buffer size must be a multiple of 2")
        for i in range(0, n, 2):
            b0 = buf[i]
            buf[i] = buf[i + 1]
            buf[i + 1] = b0

    _BYTESWAP_BACKEND = "pure_python"

__all__ = [
    "DisplayDriver",
    "alloc_buffer",
    "byteswap",
    "capabilities",
    "color332",
    "color565",
    "color565_swapped",
    "color_rgb",
    "env_bool",
    "env_get",
    "env_int",
    "env_set",
]

_DEFAULT_AUTO_REFRESH_PERIOD = 33
_DESKTOP_SCALE_MARGIN = 48
# OS window frame outside the client area (title bar / borders). Usable display
# bounds exclude the taskbar/dock but not chrome; reserve these when fitting.
_DESKTOP_WINDOW_CHROME_W = 16
_DESKTOP_WINDOW_CHROME_H = 48

# Process-local overrides for ports without ``os.environ`` / ``os.putenv``.
_overrides = {}


def env_set(name, value):
    """Set an environment variable portably (CPython, MicroPython, CircuitPython).

    Always records a process-local override so ``env_bool`` sees the value even
    when the host ``os`` module has no ``environ``. When available, also updates
    ``os.environ`` or calls ``os.putenv``.
    """
    text = "" if value is None else str(value)
    _overrides[name] = text

    import os

    environ = getattr(os, "environ", None)
    if environ is not None:
        try:
            environ[name] = text
            return
        except Exception:
            pass
    putenv = getattr(os, "putenv", None)
    if putenv is not None:
        try:
            putenv(name, text)
        except Exception:
            pass


def env_bool(name, default=False):
    """Read a truthy/falsey environment variable with a portable fallback chain."""
    raw = _env_raw(name)
    if raw is None:
        return bool(default)
    text = str(raw).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off"):
        return False
    return bool(default)


def env_get(name, default=None):
    """Read a string environment variable portably (honors ``env_set`` overrides)."""
    raw = _env_raw(name)
    if raw is None:
        return default
    return raw


def env_int(name, default=0):
    """Read an integer environment variable portably (honors ``env_set`` overrides)."""
    raw = _env_raw(name)
    if raw is None:
        return int(default)
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return int(default)


def _env_raw(name):
    if name in _overrides:
        return _overrides[name]

    import os

    environ = getattr(os, "environ", None)
    if environ is not None:
        try:
            value = environ.get(name)
        except Exception:
            value = None
        if value is not None:
            return value
    getenv = getattr(os, "getenv", None)
    if getenv is None:
        return None
    try:
        return getenv(name)
    except Exception:
        return None


def desktop_work_area(display_index=0):
    """Return ``(x, y, w, h)`` of the usable work area, or zeros if unknown.

    Prefers the OS work area (taskbar / dock excluded). Used by desktop drivers
    that do not have a native usable-bounds API (e.g. PyGame).
    """
    display_index = int(display_index)
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class _RECT(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG),
                ]

            rect = _RECT()
            # SPI_GETWORKAREA
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
                w = int(rect.right - rect.left)
                h = int(rect.bottom - rect.top)
                if w > 0 and h > 0:
                    return int(rect.left), int(rect.top), w, h
        except Exception:
            pass

    # SDL2 usable bounds when libSDL2 is loadable (CPython desktop).
    try:
        import ctypes

        sdl = None
        for name in ("SDL2", "SDL2-2.0", "libSDL2-2.0.so.0", "libSDL2.so"):
            try:
                sdl = ctypes.CDLL(name)
                break
            except OSError:
                continue
        if sdl is not None and hasattr(sdl, "SDL_GetDisplayUsableBounds"):

            class _SDL_Rect(ctypes.Structure):
                _fields_ = [
                    ("x", ctypes.c_int),
                    ("y", ctypes.c_int),
                    ("w", ctypes.c_int),
                    ("h", ctypes.c_int),
                ]

            rect = _SDL_Rect()
            fn = sdl.SDL_GetDisplayUsableBounds
            fn.argtypes = [ctypes.c_int, ctypes.POINTER(_SDL_Rect)]
            fn.restype = ctypes.c_int
            if fn(display_index, ctypes.byref(rect)) == 0 and rect.w > 0 and rect.h > 0:
                return int(rect.x), int(rect.y), int(rect.w), int(rect.h)
    except Exception:
        pass
    return 0, 0, 0, 0


def fit_scale_to_desktop(
    width,
    height,
    scale,
    desktop_w,
    desktop_h,
    *,
    margin=_DESKTOP_SCALE_MARGIN,
    chrome_w=0,
    chrome_h=0,
):
    """Return the largest scale <= *scale* so the window fits on the desktop.

    *desktop_w* / *desktop_h* should be the usable work area when available
    (taskbar / dock excluded). *margin* is padding inside that area; *chrome_w*
    / *chrome_h* reserve OS window frame outside the client (title bar, borders).
    """
    if scale <= 0 or desktop_w <= 0 or desktop_h <= 0:
        return 1.0 if scale <= 0 else scale
    max_w = desktop_w - margin - chrome_w
    max_h = desktop_h - margin - chrome_h
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


def alloc_buffer(size):
    """
    Create a new buffer of the specified size.

    Prefers SPIRAM/PSRAM when the port exposes it:

    * **MicroPython ESP32** — ``esp32.idf_heap_caps_malloc``-style helpers when
      present; otherwise a normal ``bytearray`` (large objects may still land
      in PSRAM depending on IDF heap config).
    * **CircuitPython** — GC ``bytearray``; on ESP32-S3 boards with PSRAM,
      large allocations are typically served from SPIRAM. For display surfaces,
      prefer ``displayio.Bitmap`` (see ``FBDisplay(..., bitmap=...)``) so paints
      go through C ``bitmaptools`` into PSRAM rather than Python loops.

    Args:
        size (int): The size of the buffer to create.

    Returns:
        (memoryview): The new buffer.
    """
    size = int(size)
    # MicroPython / forks that expose heap_caps to Python.
    for mod_name, fn_name, caps in (
        ("esp32", "idf_heap_caps_malloc", None),
        ("esp32", "heap_caps_malloc", 0x400),  # MALLOC_CAP_SPIRAM on IDF
    ):
        try:
            mod = __import__(mod_name)
            fn = getattr(mod, fn_name, None)
            if fn is None:
                continue
            ptr = fn(size) if caps is None else fn(size, caps)
            if ptr:
                import uctypes

                return memoryview(uctypes.bytearray_at(ptr, size))
        except Exception:
            pass

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
    # True when setting ``rotation`` remaps pixels in hardware (MADCTL) or the
    # desktop compositor (SDL/PG). False for framebuffer/RGB scanout — LVGL
    # software-rotates flush tiles instead (see add_ons/display_driver.py).
    supports_hw_rotation = False

    def __init__(self, *, quiet=False):
        self._quiet = quiet
        if not self._quiet:
            print(f"Initializing {self.__class__.__name__}...")
        gc.collect()

        self.byteswap = byteswap
        # Subclasses (e.g. PGDisplay) may set touch_scale before super().__init__
        # to match window scaling; do not clobber a preconfigured value.
        if getattr(self, "touch_scale", None) is None:
            self.touch_scale = 1.0
        self._vssa = False  # False means no vertical scroll
        self._auto_byteswap = self.requires_byteswap
        self._touch_device = None
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
