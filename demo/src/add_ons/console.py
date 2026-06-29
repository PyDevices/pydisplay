# SPDX-FileCopyrightText: 2024 Brad Barnett, 2017 boochow
#
# SPDX-License-Identifier: MIT
"""
console.py

Adapted from https://github.com/boochow/FBConsole

MIT License

Copyright (c) 2017 boochow, 2024 Brad Barnett

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import gc
import io

from multimer import Timer

try:
    import graphics as framebuf
except ImportError:
    import framebuf

# Todo: Add color changing with ANSI escape codes.  See https://pypi.org/project/colored/


class Console(io.IOBase):
    """
    Console class for MicroPython

    Requirements:
    - display_drv: Display driver object with the following methods:
        - vscrdef(tfa, vsa, bfa): Set vertical scroll definition
        - vscsad(y): Set vertical scroll start address
        - fill_rect(x, y, w, h, color): Fill rectangle with color
        - blit_rect(buf, x, y, w, h): Blit the character buffer to the display if a
          custom character writer is not provided
        - width: Width of the display
        - height: Height of the display
    Options:
    - display_drv: Display driver object with the following attributes:
        - bpp: Bits per pixel; default is 16 if not available
    - char_writer(char, x, y, fg, bg): Function to write a fixed-width character
        - Use a lambda function to pass additional arguments to the character writer.
    """

    TITLE = 0
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3

    def __init__(
        self,
        display_drv,  # Display driver object
        char_writer=None,  # Function to write a fixed-width character
        *,
        title="Console",  # Title text
        left="",  # Left status bar text
        middle="",  # Middle status bar text
        right="",  # Right status bar text
        cwidth=8,  # Character width
        lheight=8,  # Line height
        bgcolor=0,  # Background color; same as 0x0000 for 16-bit color
        fgcolor=-1,  # Foreground color; same as 0xFFFF for 16-bit color
        tfa=None,  # Top fixed area; default is line height
        bfa=None,  # Bottom fixed area; default is line height
        timer_period=1000,  # Timer period for status bar
        readobj=None,  # Object to read from, such as a keyboard queue
    ):
        self.display_drv = display_drv
        self._cwidth = cwidth
        self._lheight = lheight
        self.bgcolor = bgcolor
        self.fgcolor = fgcolor
        self._tfa = tfa if tfa else lheight
        self._bfa = bfa if bfa else lheight
        self._timer_period = timer_period
        self._readobj = readobj

        self._labels = {  # Colors are reversed in the labels
            Console.TITLE: (title, bgcolor, fgcolor),
            Console.LEFT: (left, bgcolor, fgcolor),
            Console.MIDDLE: (middle, bgcolor, fgcolor),
            Console.RIGHT: (right, bgcolor, fgcolor),
        }

        if char_writer:  # If a custom character writer is provided
            self._char_writer = char_writer  # Override the default character writer
        else:  # Otherwise, use the default character writer
            if hasattr(self.display_drv, "bpp"):  # If the display driver has a bpp attribute
                if self.display_drv.bpp == 16:
                    format = framebuf.RGB565
                elif self.display_drv.bpp == 8:
                    format = framebuf.GS8
                elif self.display_drv.bpp == 4:
                    format = framebuf.GS4_HMSB
                elif self.display_drv.bpp == 2:
                    format = framebuf.GS2_HMSB
                elif self.display_drv.bpp == 1:
                    format = framebuf.MONO_HMSB
                else:
                    raise ValueError("Unsupported bpp")
            else:  # Otherwise, default to 16-bit color
                format = framebuf.RGB565
            # Create a character buffer and frame buffer
            self._char_buf = memoryview(bytearray(self._cwidth * self._lheight * 2))
            self._char_fb = framebuf.FrameBuffer(
                self._char_buf, self._cwidth, self._lheight, format
            )

        if Timer:  # If the Timer class is available
            self._timer = Timer(-1)
        else:
            self._timer = None

        self.show()

    def show(self):
        self.width = self.display_drv.width
        self.height = self.display_drv.height
        self._vsa = self.height - self._tfa - self._bfa  # Vertical scroll area
        self.w = self.width // self._cwidth  # Number of characters per line
        self.h = self._vsa // self._lheight  # Number of lines in the scroll area
        self.display_drv.vscrdef(
            self._tfa, self._vsa, self._bfa
        )  # Set the vertical scroll definition

        self._draw_title_bar_bg(self.fgcolor)
        self._draw_status_bar_bg(self.fgcolor)
        for pos, params in self._labels.items():
            if isinstance(params[0], str):
                self._write_label(pos, params[0], params[1], params[2])

        if self._timer:
            self._timer.init(mode=Timer.PERIODIC, period=self._timer_period, callback=self._tick)

        self.cls()

    def cls(self):
        self.x = 0
        self.y = 0
        self.y_end = 0
        self._scroll_pos = self._tfa
        self.display_drv.vscsad(self._scroll_pos)
        self.display_drv.fill_rect(0, self._tfa, self.width, self._vsa, self.bgcolor)

    def hide(self):
        if self._timer:
            self._timer.deinit()
        self.display_drv.vscsad(0)
        self.display_drv.fill_rect(0, 0, self.width, self.height, 0)

    def label(self, pos, param, fg=0, bg=-1):
        self._labels[pos] = (param, fg, bg)
        if isinstance(param, str):
            self._write_label(pos, param, fg, bg)

    def _write_label(self, pos, text, fg, bg):
        if pos == Console.TITLE:
            self._draw_title_bar_bg(bg)
            self._write_str(text, (self.w - len(text)) // 2, self._tfa - self._lheight, fg, bg)
        elif pos == Console.LEFT:
            self.display_drv.fill_rect(
                0, self._tfa + self._vsa, self.width // 3, self._lheight, bg
            )
            self._write_str(text, 1, self._tfa + self._vsa, fg, bg)
        elif pos == Console.MIDDLE:
            self.display_drv.fill_rect(
                self.display_drv.width // 3,
                self._tfa + self._vsa,
                self.width // 3,
                self._lheight,
                bg,
            )
            self._write_str(text, (self.w - len(text)) // 2, self._tfa + self._vsa, fg, bg)
        elif pos == Console.RIGHT:
            self.display_drv.fill_rect(
                self.display_drv.width * 2 // 3,
                self._tfa + self._vsa,
                self.width // 3,
                self._lheight,
                bg,
            )
            self._write_str(text, self.w - len(text) - 1, self._tfa + self._vsa, fg, bg)

    def _write_str(self, text, x, y, fg, bg):
        for i, char in enumerate(text):
            self._char_writer(char, (x + i) * self._cwidth, y, fg, bg)

    def _draw_title_bar_bg(self, color=-1):
        self.display_drv.fill_rect(0, self._tfa - self._lheight, self.width, self._lheight, color)

    def _draw_status_bar_bg(self, color=-1):
        self.display_drv.fill_rect(0, self._tfa + self._vsa, self.width, self._lheight, color)

    def _tick(self, timer):
        gc.collect()
        for pos, params in self._labels.items():
            if not isinstance(params[0], str):
                self._write_label(pos, params[0](), params[1], params[2])

    def read(self, nbytes=1):
        """dupterm input: delegate to readobj or block on the primary stdin fd."""
        if self._readobj is not None:
            if hasattr(self._readobj, "read"):
                return self._readobj.read(nbytes)
            buf = bytearray(nbytes if nbytes else 1)
            got = self.readinto(buf, nbytes)
            if got:
                return bytes(buf[:got])
            return b""
        try:
            import sys

            n = nbytes if nbytes else 1
            return sys.stdin.buffer.read(n)
        except Exception:
            return b""

    def readinto(self, buf, nbytes=0):
        if self._readobj is not None and hasattr(self._readobj, "readinto"):
            return self._readobj.readinto(buf, nbytes)
        data = self.read(nbytes or len(buf))
        if not data:
            return 0
        n = min(len(buf), len(data))
        buf[:n] = data[:n]
        return n

    def write(self, buf, fg=None, bg=None):
        fg = self.fgcolor if fg is None else fg
        bg = self.bgcolor if bg is None else bg
        if isinstance(buf, str):
            buf = buf.encode()
        self._draw_cursor(self.bgcolor)
        i = 0
        while i < len(buf):
            c = buf[i]
            if c == 0x1B:
                i += 1
                esc = i
                while chr(buf[i]) in "[;0123456789":
                    i += 1
                c = buf[i]
                if c == 0x4B and i == esc + 1:  # ESC [ K
                    self._clear_cursor_eol()
                elif c == 0x44:  # ESC [ n D
                    for _ in range(self._esq_read_num(buf, i - 1)):
                        self._backspace()
            else:
                self._putc(c, fg, bg)
            i += 1
        self._draw_cursor(self.fgcolor)
        return len(buf)

    def _putc(self, c, fg, bg):
        c = chr(c)
        if c == "\n":
            self._newline()
        elif c == "\x08":
            self._backspace()
        elif c >= " ":
            self._char_writer(c, self._x_pos, self._y_pos, fg, bg)
            self.x += 1
            if self.x >= self.w:
                self._newline()

    def _char_writer(self, char, x, y, fg, bg):
        self._char_fb.fill(bg)
        self._char_fb.text(char, 0, 0, fg)
        self.display_drv.blit_rect(self._char_buf, x, y, self._cwidth, self._lheight)

    def _esq_read_num(self, buf, pos):
        digit = 1
        n = 0
        while buf[pos] != 0x5B:
            n += digit * (buf[pos] - 0x30)
            pos -= 1
            digit *= 10
        return n

    def _newline(self):
        self.x = 0
        self.y += 1
        if self.y >= self.h:
            self._scroll_pos = (((self.y % self.h) + 1) * self._lheight) + self._tfa
            self.display_drv.vscsad(self._scroll_pos)
            self.display_drv.fill_rect(0, self._y_pos, self.width, self._lheight, 0)
        self.y_end = self.y

    def _backspace(self):
        if self.x == 0:
            if self.y > 0:
                self.y -= 1
                self.x = self.w - 1
        else:
            self.x -= 1

    def _draw_cursor(self, color):
        self.display_drv.fill_rect(
            self._x_pos, self._y_pos + self._lheight - 2, self._cwidth, 1, color
        )

    def _clear_cursor_eol(self):
        self.display_drv.fill_rect(
            self._x_pos,
            self._y_pos,
            self.width - self._x_pos,
            self._lheight,
            self.bgcolor,
        )
        for l in range(self.y + 1, self.y_end + 1):
            self.display_drv.fill_rect(
                0, l * self._lheight, self.width, self._lheight, self.bgcolor
            )
        self.y_end = self.y

    @property
    def _x_pos(self):
        return self.x * self._cwidth

    @property
    def _y_pos(self):
        return ((self.y % self.h) * self._lheight) + self._tfa

    def __del__(self):
        self.hide()
