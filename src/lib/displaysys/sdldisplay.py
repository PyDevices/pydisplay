# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
displaysys.sdldisplay — SDL2 desktop display driver.
"""

from sys import implementation

import usdl2

from displaysys import DisplayDriver, color_rgb, default_quit_chord
from eventsys import events

_NATIVE_USDL2 = not hasattr(usdl2, "_USE_FFI")

_JOYSTICK_API = (
    "SDL_InitSubSystem",
    "SDL_JoystickClose",
    "SDL_JoystickInstanceID",
    "SDL_JoystickOpen",
    "SDL_NumJoysticks",
)
_HAS_JOYSTICK_API = all(hasattr(usdl2, name) for name in _JOYSTICK_API)

if implementation.name == "cpython":
    import ctypes

    uses_native_event = True
    uses_ctypes_blit = True
elif implementation.name == "circuitpython":
    uses_native_event = True
    uses_ctypes_blit = False
else:
    uses_native_event = _NATIVE_USDL2
    uses_ctypes_blit = False

# Linux c_lflag bits (MicroPython termios has no ECHO/ICANON constants).
_TTY_ICANON = 0x002
_TTY_ECHO = 0x008
_saved_tty = None


def _save_tty() -> None:
    """Save stdin termios before SDL_Init may alter the controlling terminal."""
    global _saved_tty
    try:
        import os
        import termios

        if os.isatty(0):
            _saved_tty = termios.tcgetattr(0)
    except Exception:
        _saved_tty = None


def _restore_tty() -> None:
    """Restore stdin termios saved at SDL init."""
    global _saved_tty
    if _saved_tty is None:
        return
    try:
        import termios

        termios.tcsetattr(0, termios.TCSANOW, _saved_tty)
    except Exception:
        pass
    _saved_tty = None


def _ensure_tty_sane() -> None:
    """
    Ensure canonical mode and echo are enabled before returning a TTY to the shell.

    SDL_Quit restores the snapshot taken at SDL_Init, which may still reflect a
    no-echo REPL state.  Forcing sane flags avoids a shell prompt that accepts
    input but does not echo typed characters.
    """
    try:
        import termios

        attr = termios.tcgetattr(0)
        attr[3] |= _TTY_ICANON | _TTY_ECHO
        termios.tcsetattr(0, termios.TCSANOW, attr)
    except Exception:
        try:
            import os
            import sys

            # ``stty`` is Unix-only; ``os.system`` on win32 spawns CMD.EXE and
            # errors when micropython.exe is launched from a WSL UNC cwd.
            if sys.platform == "win32":
                return
            os.system("stty sane 2>/dev/null")
        except Exception:
            pass


_event = usdl2.SDL_Event()

# Open joystick handles, keyed by SDL instance id, kept referenced so SDL keeps
# delivering their events.
_joysticks = {}


def _init_joysticks() -> None:
    """
    Initialize the joystick subsystem and open all connected joysticks.

    Joysticks must be opened for SDL to deliver their events.  Devices connected
    after startup are not hot-plugged (connect controllers before launching).
    Failures are ignored so a missing/headless joystick subsystem never breaks
    the display.
    """
    if not _HAS_JOYSTICK_API:
        return
    try:
        if usdl2.SDL_InitSubSystem(usdl2.SDL_INIT_JOYSTICK) != 0:
            return
        for i in range(usdl2.SDL_NumJoysticks()):
            handle = usdl2.SDL_JoystickOpen(i)
            if handle:
                _joysticks[usdl2.SDL_JoystickInstanceID(handle)] = handle
    except Exception:
        pass


def _close_joysticks() -> None:
    """Close any opened joysticks."""
    if not _HAS_JOYSTICK_API:
        return
    for handle in _joysticks.values():
        try:
            usdl2.SDL_JoystickClose(handle)
        except Exception:
            pass
    _joysticks.clear()


def _hat_xy(value):
    """Convert an SDL hat bitmask to an (x, y) tuple matching PyGame's get_hat()."""
    x = (1 if value & usdl2.SDL_HAT_RIGHT else 0) - (1 if value & usdl2.SDL_HAT_LEFT else 0)
    y = (1 if value & usdl2.SDL_HAT_UP else 0) - (1 if value & usdl2.SDL_HAT_DOWN else 0)
    return (x, y)


def poll_event():
    """
    Poll for one pending event.

    Returns:
        Optional[events]: One eventsys event, or ``None``.
    """
    global _event
    if usdl2.SDL_PollEvent(_event):
        if uses_native_event:
            if _event.type in events.filter:
                return _convert(usdl2.SDL_Event(_event))
        else:
            if int.from_bytes(_event[:4], "little") in events.filter:
                return _convert(usdl2.SDL_Event(_event))
    return None


def get_events():
    """
    Drain all pending events from the SDL queue.

    Returns:
        list | None: A list of eventsys events, or ``None`` if the queue was empty.
    """
    global _event
    eventlist = []
    while usdl2.SDL_PollEvent(_event):
        if uses_native_event:
            if _event.type in events.filter:
                eventlist.append(_convert(usdl2.SDL_Event(_event)))
        else:
            if int.from_bytes(_event[:4], "little") in events.filter:
                eventlist.append(_convert(usdl2.SDL_Event(_event)))
    return eventlist if len(eventlist) > 0 else None


def _convert(e):
    # Convert an SDL event to a Pygame event
    if e.type == usdl2.SDL_MOUSEMOTION:
        l = 1 if e.motion.state & usdl2.SDL_BUTTON_LMASK else 0  # noqa: E741
        m = 1 if e.motion.state & usdl2.SDL_BUTTON_MMASK else 0
        r = 1 if e.motion.state & usdl2.SDL_BUTTON_RMASK else 0
        evt = events.Motion(
            e.type,
            (e.motion.x, e.motion.y),
            (e.motion.xrel, e.motion.yrel),
            (l, m, r),
            e.motion.which != 0,
            e.motion.windowID,
        )
    elif e.type in (usdl2.SDL_MOUSEBUTTONDOWN, usdl2.SDL_MOUSEBUTTONUP):
        evt = events.Button(
            e.type,
            (e.button.x, e.button.y),
            e.button.button,
            e.button.which != 0,
            e.button.windowID,
        )
    elif e.type == usdl2.SDL_MOUSEWHEEL:
        evt = events.Wheel(
            e.type,
            e.wheel.direction != 0,
            e.wheel.x,
            e.wheel.y,
            e.wheel.preciseX,
            e.wheel.preciseY,
            e.wheel.which != 0,
            e.wheel.windowID,
        )
    elif e.type in (usdl2.SDL_KEYDOWN, usdl2.SDL_KEYUP):
        name = usdl2.SDL_GetKeyName(e.key.keysym.sym)
        evt = events.Key(
            e.type,
            name,
            e.key.keysym.sym,
            e.key.keysym.mod,
            e.key.keysym.scancode,
            e.key.windowID,
        )
    elif e.type == usdl2.SDL_JOYAXISMOTION:
        # Normalize the Sint16 axis value to -1.0..1.0 to match PyGame/Gamepad.
        evt = events.JoyAxisMotion(e.type, e.jaxis.which, e.jaxis.axis, e.jaxis.value / 32767)
    elif e.type == usdl2.SDL_JOYBALLMOTION:
        evt = events.JoyBallMotion(
            e.type, e.jball.which, e.jball.ball, (e.jball.xrel, e.jball.yrel)
        )
    elif e.type == usdl2.SDL_JOYHATMOTION:
        evt = events.JoyHatMotion(e.type, e.jhat.which, e.jhat.hat, _hat_xy(e.jhat.value))
    elif e.type == usdl2.SDL_JOYBUTTONDOWN:
        evt = events.JoyButtonDown(e.type, e.jbutton.which, e.jbutton.button)
    elif e.type == usdl2.SDL_JOYBUTTONUP:
        evt = events.JoyButtonUp(e.type, e.jbutton.which, e.jbutton.button)
    elif e.type == usdl2.SDL_QUIT:
        evt = events.Quit(e.type)
    else:
        evt = events.Unknown(e.type)
    return evt


def retcheck(retvalue):
    # Check the return value of an SDL function and raise an exception if it's not 0
    if retvalue:
        raise RuntimeError(usdl2.SDL_GetError())


def _hard_process_exit(code: int = 0) -> None:
    """Terminate immediately without SDL teardown (kit subprocesses)."""
    try:
        import usdl2

        usdl2.process_exit(code)
    except Exception:
        pass
    try:
        import ffi

        ffi.open("libc.so.6").func("v", "_exit", "i")(code)
    except Exception:
        pass
    try:
        import os

        os._exit(code)
    except Exception:
        pass
    raise SystemExit(code)


class SDLDisplay(DisplayDriver):
    """
    A class to emulate an LCD using SDL2.
    Provides scrolling and rotation functions similar to an LCD.  The .texture
    object functions as the LCD's internal memory.

    Args:
        width (int, optional): The width of the display. Defaults to 320.
        height (int, optional): The height of the display. Defaults to 240.
        rotation (int, optional): The rotation of the display. Defaults to 0.
        color_depth (int, optional): The color depth of the display. Defaults to 16.
        title (str, optional): The title of the display window. Defaults to "SDL2 Display".
        scale (float, optional): The scale of the display. Defaults to 1.0.
        window_flags (int, optional): The flags for creating the display window. Defaults to SDL_WINDOW_SHOWN.
        render_flags (int, optional): The flags for creating the renderer. Defaults to SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC.
        x (int, optional): The x-coordinate of the display window's position. Defaults to SDL_WINDOWPOS_CENTERED.
        y (int, optional): The y-coordinate of the display window's position. Defaults to SDL_WINDOWPOS_CENTERED.
    """

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
    ):
        self._width = width
        self._height = height
        self._rotation = rotation
        self.color_depth = color_depth
        self._title = title
        self._window_flags = window_flags
        self._scale = scale
        self.touch_scale = 1.0
        self.quit_chord = default_quit_chord()
        self._buffer = None
        self._requires_byteswap = False

        # CircuitPython + usdl2 accelerated GL cannot attach swapped-dimension render
        # targets during rotation (SetRenderTarget -> glFramebufferTexture2DEXT).
        if implementation.name == "circuitpython" and (
            render_flags & usdl2.SDL_RENDERER_ACCELERATED
        ):
            render_flags = (
                render_flags & ~usdl2.SDL_RENDERER_ACCELERATED
            ) | usdl2.SDL_RENDERER_SOFTWARE

        # Determine the pixel format
        if color_depth == 32:
            self._px_format = usdl2.SDL_PIXELFORMAT_ARGB8888
        elif color_depth == 24:
            self._px_format = usdl2.SDL_PIXELFORMAT_RGB888
        elif color_depth == 16:
            self._px_format = usdl2.SDL_PIXELFORMAT_RGB565
        else:
            raise ValueError("Unsupported color_depth")

        _save_tty()
        retcheck(usdl2.SDL_Init(usdl2.SDL_INIT_EVERYTHING))
        _init_joysticks()
        self._window = usdl2.SDL_CreateWindow(
            self._title.encode(),
            x,
            y,
            int(self.width * self._scale),
            int(self.height * self._scale),
            self._window_flags,
        )
        if not self._window:
            raise RuntimeError(f"{usdl2.SDL_GetError()}")
        self._renderer = usdl2.SDL_CreateRenderer(self._window, -1, render_flags)
        if not self._renderer:
            raise RuntimeError(f"{usdl2.SDL_GetError()}")

        self._buffer = usdl2.SDL_CreateTexture(
            self._renderer,
            self._px_format,
            usdl2.SDL_TEXTUREACCESS_TARGET,
            self.width,
            self.height,
        )
        if not self._buffer:
            raise RuntimeError(f"{usdl2.SDL_GetError()}")
        retcheck(usdl2.SDL_SetTextureBlendMode(self._buffer, usdl2.SDL_BLENDMODE_NONE))

        auto_refresh = True
        if implementation.name == "micropython":
            try:
                from multimer import needs_pump

                if needs_pump():
                    auto_refresh = False
            except ImportError:
                pass

        super().__init__(auto_refresh=auto_refresh)

    ############### Required API Methods ################

    def init(self) -> None:
        """
        Initializes the display instance.  Called by __init__ and rotation setter.
        """
        retcheck(
            usdl2.SDL_SetWindowSize(
                self._window,
                int(self.width * self._scale),
                int(self.height * self._scale),
            )
        )
        retcheck(usdl2.SDL_RenderSetLogicalSize(self._renderer, self.width, self.height))

        super().vscrdef(
            0, self.height, 0
        )  # Set the vertical scroll definition without calling .render()
        self.vscsad(False)  # Scroll offset; set to False to disable scrolling

    def blit_rect(self, buffer: memoryview, x: int, y: int, w: int, h: int):
        """
        Blits a buffer to the display.

        Args:
            buffer (memoryview): The buffer to blit.
            x (int): The x-coordinate of the buffer.
            y (int): The y-coordinate of the buffer.
            w (int): The width to blit.
            h (int): The height to blit.

        Returns:
            (tuple): A tuple containing the x, y, w, h values.
        """
        if not self._sdl_active():
            return (x, y, w, h)
        pitch = int(w * self.color_depth // 8)
        if len(buffer) != pitch * h:
            raise ValueError("Buffer size does not match dimensions")
        blitRect = usdl2.SDL_Rect(x, y, w, h)
        if uses_ctypes_blit:
            if isinstance(buffer, memoryview) or type(buffer) is bytearray:
                buffer_array = (ctypes.c_ubyte * len(buffer)).from_buffer(buffer)
            else:
                raise ValueError(
                    f"Buffer is of type {type(buffer)} instead of memoryview or bytearray"
                )
            buffer_ptr = ctypes.c_void_p(ctypes.addressof(buffer_array))
            retcheck(usdl2.SDL_UpdateTexture(self._buffer, blitRect, buffer_ptr, pitch))
        else:
            retcheck(usdl2.SDL_UpdateTexture(self._buffer, blitRect, buffer, pitch))
        self.render(blitRect)
        return (x, y, w, h)

    def fill_rect(self, x: int, y: int, w: int, h: int, c: int):
        """
        Fill a rectangle with a color.

        Renders to the texture instead of directly to the window
        to facilitate scrolling and scaling.

        Args:
            x (int): The x-coordinate of the rectangle.
            y (int): The y-coordinate of the rectangle.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.
            c (int): The color of the rectangle.

        Returns:
            (tuple): A tuple containing the x, y, w, h values
        """
        fillRect = usdl2.SDL_Rect(x, y, w, h)
        r, g, b = color_rgb(c)

        try:
            retcheck(usdl2.SDL_SetRenderTarget(self._renderer, None))
        except RuntimeError:
            pass
        retcheck(
            usdl2.SDL_SetRenderTarget(self._renderer, self._buffer)
        )  # Set the render target to the texture
        retcheck(
            usdl2.SDL_SetRenderDrawColor(self._renderer, r, g, b, 255)
        )  # Set the color to fill the rectangle
        retcheck(
            usdl2.SDL_RenderFillRect(self._renderer, fillRect)
        )  # Fill the rectangle on the texture
        retcheck(
            usdl2.SDL_SetRenderTarget(self._renderer, None)
        )  # Reset the render target back to the window
        self.render(fillRect)
        return (x, y, w, h)

    def pixel(self, x: int, y: int, c: int):
        """
        Set a pixel on the display.

        Args:
            x (int): The x-coordinate of the pixel.
            y (int): The y-coordinate of the pixel.
            c (int): The color of the pixel.

        Returns:
            (tuple): A tuple containing the x, y values.
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
        self.render()

    def vscsad(self, vssa=None) -> int:
        """
        Set or get the vertical scroll start address.

        Args:
            vssa (int): The vertical scroll start address. Defaults to None.

        Returns:
            int: The vertical scroll start address.
        """
        if vssa is not None:
            super().vscsad(vssa)
            self.render()
        return self._vssa

    def _rotation_helper(self, value):
        """
        Creates a new texture to use as the buffer and copies the old one,
        applying rotation with SDL_RenderCopyEx.  Destroys the old buffer.

        Args:
            value (int): The new rotation value.
        """

        if (angle := (value % 360) - (self._rotation % 360)) != 0:
            if uses_native_event:
                tempBuffer = usdl2.SDL_CreateTexture(
                    self._renderer,
                    self._px_format,
                    usdl2.SDL_TEXTUREACCESS_TARGET,
                    self.height,
                    self.width,
                )
                if not tempBuffer:
                    raise RuntimeError(f"{usdl2.SDL_GetError()}")

                retcheck(usdl2.SDL_SetTextureBlendMode(tempBuffer, usdl2.SDL_BLENDMODE_NONE))
                retcheck(usdl2.SDL_SetRenderTarget(self._renderer, tempBuffer))
                if abs(angle) != 180:
                    dstrect = usdl2.SDL_Rect(
                        (self.height - self.width) // 2,
                        (self.width - self.height) // 2,
                        self.width,
                        self.height,
                    )
                else:
                    dstrect = None
                retcheck(
                    usdl2.SDL_RenderCopyEx(
                        self._renderer, self._buffer, None, dstrect, angle, None, 0
                    )
                )
                retcheck(usdl2.SDL_SetRenderTarget(self._renderer, None))
                retcheck(usdl2.SDL_DestroyTexture(self._buffer))
                self._buffer = tempBuffer
            else:
                retcheck(usdl2.SDL_DestroyTexture(self._buffer))
                self._buffer = usdl2.SDL_CreateTexture(
                    self._renderer,
                    self._px_format,
                    usdl2.SDL_TEXTUREACCESS_TARGET,
                    self.height,
                    self.width,
                )
                if not self._buffer:
                    raise RuntimeError(f"{usdl2.SDL_GetError()}")
                retcheck(usdl2.SDL_SetTextureBlendMode(self._buffer, usdl2.SDL_BLENDMODE_NONE))

    ############### Class Specific Methods ##############

    def _sdl_active(self) -> bool:
        """True while SDL video is initialized and this driver is live."""
        if getattr(self, "_deinitialized", False):
            return False
        return self._renderer is not None and self._window is not None

    def render(self, renderRect=None):
        """
        Render the display.  Automatically called after blitting or filling the display.

        Args:
            renderRect (Optional[SDL_Rect], optional): The rectangle to render. Defaults to None.
        """
        if not self._sdl_active():
            return
        # Single SDL_RenderCopy was disabled: not working on Chromebooks, Ubuntu, Raspberry Pi OS.
        y_start = self.vscsad()
        if self._tfa > 0:
            tfaRect = usdl2.SDL_Rect(0, 0, self.width, self._tfa)
            retcheck(usdl2.SDL_RenderCopy(self._renderer, self._buffer, tfaRect, tfaRect))

        vsaTopHeight = self._vsa + self._tfa - y_start
        vsaTopSrcRect = usdl2.SDL_Rect(0, y_start, self.width, vsaTopHeight)
        vsaTopDestRect = usdl2.SDL_Rect(0, self._tfa, self.width, vsaTopHeight)
        retcheck(usdl2.SDL_RenderCopy(self._renderer, self._buffer, vsaTopSrcRect, vsaTopDestRect))

        vsaBtmHeight = self._vsa - vsaTopHeight
        vsaBtmSrcRect = usdl2.SDL_Rect(0, self._tfa, self.width, vsaBtmHeight)
        vsaBtmDestRect = usdl2.SDL_Rect(0, self._tfa + vsaTopHeight, self.width, vsaBtmHeight)
        retcheck(usdl2.SDL_RenderCopy(self._renderer, self._buffer, vsaBtmSrcRect, vsaBtmDestRect))

        if self._bfa > 0:
            bfaRect = usdl2.SDL_Rect(0, self._tfa + self._vsa, self.width, self._bfa)
            retcheck(usdl2.SDL_RenderCopy(self._renderer, self._buffer, bfaRect, bfaRect))

    def show(self, _timer=None) -> None:
        """
        Show the display.
        """
        if not self._sdl_active():
            return
        usdl2.SDL_RenderPresent(self._renderer)

    def _deinit(self) -> None:
        """Release SDL resources."""
        _close_joysticks()
        if self._buffer is not None:
            usdl2.SDL_DestroyTexture(self._buffer)
            self._buffer = None
        if self._renderer is not None:
            usdl2.SDL_DestroyRenderer(self._renderer)
            self._renderer = None
        if self._window is not None:
            usdl2.SDL_DestroyWindow(self._window)
            self._window = None
        usdl2.SDL_Quit()
        _restore_tty()
        _ensure_tty_sane()

    def quit(self, code: int = 0, force: bool = False) -> None:
        """Release SDL resources (REPL-safe unless ``force=True``)."""
        if not force:
            self.deinit()
            return
        try:
            self.deinit()
        except Exception:
            pass
        try:
            _ensure_tty_sane()
        except Exception:
            pass
        _hard_process_exit(code)

    def force_quit(self, code: int = 0) -> None:
        """Release SDL resources then hard-exit the process.

        On MicroPython and CircuitPython, ``SDL_Quit`` during subprocess shutdown
        can SIGSEGV; skip SDL teardown and ``_exit`` immediately after restoring
        the TTY (kit harnesses and other short-lived desktop runs).
        """
        import sys

        if sys.implementation.name in ("micropython", "circuitpython"):
            try:
                _restore_tty()
                _ensure_tty_sane()
            except Exception:
                pass
            _hard_process_exit(code)
        self.quit(code, force=True)
