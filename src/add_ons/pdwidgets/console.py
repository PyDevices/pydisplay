# SPDX-FileCopyrightText: 2024 Brad Barnett, 2017 boochow
#
# SPDX-License-Identifier: MIT
"""
`pdwidgets.console.py`
====================================================

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

import io

from . import TEXT_SIZE, TEXT_WIDTH, Widget

# Todo: Add color changing with ANSI escape codes.  See https://pypi.org/project/colored/


class Console(io.IOBase, Widget):
    def __init__(
        self,
        parent,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        by_char=False,
        margin=1,
        text_height=TEXT_SIZE.LARGE,
        scale=1,
        font_data=None,
    ):
        self.margin = margin
        if text_height not in TEXT_SIZE:
            raise ValueError("Text height must be 8, 14 or 16 pixels.")
        self.text_height = text_height
        self.scale = scale
        self.font_data = font_data
        self._char_width = TEXT_WIDTH * scale
        self._char_height = text_height * scale
        self._read_obj = None
        if parent.display.vsa % self._char_height:
            raise ValueError("VSA must be a multiple of the character height.")
        self.dirty_areas = []
        self.by_char = by_char
        Widget.__init__(self, parent, *parent.display.vsa_area, fg, bg, visible, value)
        self.columns = (
            self.width - 2 * margin
        ) // self._char_width  # Number of characters per line
        self.rows = self.height // self._char_height  # Number of lines
        self._reset_cursor()

    def _reset_cursor(self):
        self.cursor_col = 0
        self.cursor_row = 0
        self.cursor_max_row = 0
        self.display.vscroll = 0

    def clear(self):
        self.dirty_areas.append(self.display.framebuf.fill_rect(*self.area, self.bg))
        self._reset_cursor()

    def readinto(self, buf, nbytes=0):  # overrides io.IOBase.readinto
        if self._readobj is not None:
            return self._readobj.readinto(buf, nbytes)
        else:
            return None

    def write(self, buf, fg=None, bg=None):  # overrides io.IOBase.write
        fg = fg if fg is not None else self.parent.fg
        bg = bg if bg is not None else self.parent.bg
        if isinstance(buf, str):
            buf = buf.encode()
        self._draw_cursor(self.bg)  # Erase cursor
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
                self._put_char(c, fg, bg)
            i += 1
        self._draw_cursor(self.fg)  # Redraw cursor
        self.draw()
        return len(buf)

    def _put_char(self, c, fg, bg):
        c = chr(c)
        if c == "\n":
            self._newline()
            self.draw()
        elif c == "\x08":
            self._backspace()
        elif c >= " ":
            if bg is not None:
                self.display.framebuf.fill_rect(
                    self._x_pos, self._cursor_y_pos, self._char_width, self._char_height, bg
                )
            self.dirty_areas.append(
                self.display.framebuf.text(
                    c,
                    self._x_pos,
                    self._cursor_y_pos,
                    fg,
                    height=self.text_height,
                    scale=self.scale,
                    font_data=self.font_data,
                )
            )
            if self.by_char:
                self.draw()
            self.cursor_col += 1
            if self.cursor_col >= self.columns:
                self._newline()

    def _esq_read_num(self, buf, pos):
        digit = 1
        n = 0
        while buf[pos] != 0x5B:
            n += digit * (buf[pos] - 0x30)
            pos -= 1
            digit *= 10
        return n

    def _newline(self):
        self.cursor_col = 0
        self.cursor_row += 1
        if self._cursor_y_rel > self.display.vsa - self._char_height:
            self.display.vscroll = (self._cursor_y_rel + self._char_height) % self.display.vsa
            self.dirty_areas.append(
                self.display.framebuf.fill_rect(
                    0, self._cursor_y_pos, self.width, self._char_height, 0
                )
            )
        self.cursor_max_row = self.cursor_row

    def _backspace(self):
        if self.cursor_col == 0:
            if self.cursor_row > 0:
                self.cursor_row -= 1
                self.cursor_col = self.columns - 1
        else:
            self.cursor_col -= 1

    def _draw_cursor(self, color):
        self.dirty_areas.append(
            self.display.framebuf.fill_rect(
                self._x_pos, self._cursor_y_pos + self._char_height - 2, self._char_width, 1, color
            )
        )

    def _clear_cursor_eol(self):
        self.dirty_areas.append(
            self.display.framebuf.fill_rect(
                self._x_pos,
                self._cursor_y_pos,
                self.width - self._x_pos,
                self._char_height,
                self.bg,
            )
        )
        for line in range(self.cursor_row + 1, self.cursor_max_row + 1):
            self.dirty_areas.append(
                self.display.framebuf.fill_rect(
                    0, line * self._char_height, self.width, self._char_height, self.bg
                )
            )
        self.cursor_max_row = self.cursor_row

    @property
    def _x_pos(self):
        return self.cursor_col * self._char_width

    @property
    def _cursor_y_rel(self):
        return self.cursor_row * self._char_height

    @property
    def _cursor_y_pos(self):
        return (self._cursor_y_rel % self.display.vsa) + self.display.tfa

    def draw(self):
        if self.dirty_areas:
            dirty = self.dirty_areas[0]
            for area in self.dirty_areas[1:]:
                dirty += area
            self.dirty_areas = []
            self.display.refresh(dirty)
