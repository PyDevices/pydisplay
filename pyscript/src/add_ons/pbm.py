"""
A class to handle PBM files - WIP - Not working yet

Example:
    from board_config import display_drv
    from framebuf import FrameBuffer, RGB565
    from pbm import PBM

    logo = PBM("examples/assets/micropython.pbm")

    # render direct to the display with fg and bg colors
    logo.render(display_drv, 0, 0, 0xFFFF, 0x0000)

    # render direct to the display with fg and transparent bg
    logo.render(display_drv, 0, display_drv.height//2, 0xFFFF)

    # blit to a frame buffer
    buf = bytearray(logo.width * logo.height * 2)
    fb = FrameBuffer(buf, logo.width, logo.height, RGB565)
    palette = FrameBuffer(memoryview(bytearray(2 * 2)), 2, 1, RGB565)
    palette.pixel(0, 0, 0x0FF0)
    palette.pixel(1, 0, 0xFFFF)
    fb.blit(logo, 0, 0, palette.pixel(0, 0), palette)

    # blit the frame buffer to the display
    display_drv.blit_rect(buf, display_drv.width * 2 // 3, 0, logo.width, logo.height)

    # blit the frame buffer to the display with transparent bg
    display_drv.blit_transparent(buf, display_drv.width * 2 // 3, display_drv.height//2, logo.width, logo.height, 0x000F)

"""

import os

from graphics import MONO_HLSB, RGB565, FrameBuffer

sep = os.sep if hasattr(os, "sep") else "/"  # PyScipt doesn't have os.sep


class PBM:
    """Monochrome PBM (P4) bitmap; render to any canvas via ``render()``."""

    def __init__(
        self, filename=None, fg=0xFFFF, bg=0x0000, format=RGB565, width=None, height=None
    ):
        self._palette = FrameBuffer(memoryview(bytearray(2 * 2)), 2, 1, format)
        self._format = MONO_HLSB
        self.bg = bg
        self.fg = fg
        if filename and not (width or height):
            self._read_file(filename)
        elif width and height:
            self._filename = None
            self._buffer = memoryview(bytearray(width * height // 8))
            self._width = width
            self._height = height
        else:
            raise ValueError("PBM:  Invalid arguments - must provide filename or width and height")
        self._fb = FrameBuffer(self._buffer, self._width, self._height, MONO_HLSB)

    def fill(self, c):
        return self._fb.fill(c)

    def pixel(self, x, y, c=None):
        if c is None:
            return self._fb.pixel(x, y)
        return self._fb.pixel(x, y, c)

    def _read_file(self, filename):
        self._filename = filename
        with open(self._filename, "rb") as f:
            # Read the header
            header = f.read(3)[:2]
            if header != b"P1" and header != b"P4":
                raise ValueError("Invalid PBM header")
            # Read the data
            if header == b"P1":
                # ASCII
                print("ASCII")
                raise NotImplementedError("ASCII PBM files are not supported yet")
            elif header == b"P4":
                data = (
                    f.read()
                )  # Read the rest as binary, since MicroPython can't do readline here
                while data[0] == 35:  # Ignore comment lines starting with b'#'
                    data = data.split(b"\n", 1)[1]
                dims, data = data.split(b"\n", 1)  # Assumes no comments after dimensions
                self._width, self._height = map(int, dims.split())
                self._buffer = memoryview(bytearray((self._width + 7) // 8 * self._height))
                self._buffer[:] = data

    @property
    def format(self):
        return self._format

    def render(self, canvas, x, y, fg=0, bg=None):
        col = row = 0
        for i in range(len(self._buffer)):
            for bit in self._bitgen(self._buffer[i]):
                if bit:
                    canvas.pixel(x + col, y + row, fg)
                elif bg is not None:
                    canvas.pixel(x + col, y + row, bg)
                col += 1
                if col >= self._width:
                    col = 0
                    row += 1

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def buffer(self):
        return self._buffer

    @property
    def fg(self):
        return self._palette.pixel(1, 0)

    @fg.setter
    def fg(self, color):
        self._palette.pixel(1, 0, color)

    @property
    def bg(self):
        return self._palette.pixel(0, 0)

    @bg.setter
    def bg(self, color):
        self._palette.pixel(0, 0, color)

    @property
    def palette(self):
        return self._palette

    @staticmethod
    def _bitgen(b):
        """
        generator to iterate over the bits in a byte (character)
        """
        # reverse bit order
        b = (b & 0xF0) >> 4 | (b & 0x0F) << 4
        b = (b & 0xCC) >> 2 | (b & 0x33) << 2
        b = (b & 0xAA) >> 1 | (b & 0x55) << 1
        for i in range(8):
            yield (b >> i) & 1

    def __str__(self):
        return f"PBM({self._filename}, {self.fg}, {self.bg})"

    def __repr__(self):
        return f"PBM({self._filename}, {self.fg}, {self.bg})"

    def save(self, filename):
        with open(filename, "wb") as f:
            f.write(b"P4\n")
            f.write(f"{self._width} {self._height}\n")
            f.write(self._buffer)

    def export(self):
        """
        Export the PBM file as a Python file with the bitmap data

        EXPERIMENTAL - Not complete.  Haven't found a use for it yet.
        """
        src_filename_ext = self._filename.split(sep)[-1]
        directory = ""  # self._filename.replace(src_filename_ext, "")
        filename = src_filename_ext.replace(".pbm", "")
        out = []

        out.append(f"WIDTH = {self._width}")
        out.append(f"HEIGHT = {self._height}")
        out.append("BPP = 1")
        out.append(f"PALLETTE = [{hex(self.bg)}, {hex(self.fg)}]")
        out.append("_bitmap =\\")

        bytes_per_row = len(self._buffer) // self._height
        for y in range(self._height):
            row = "b'"
            for x in range(bytes_per_row):
                row += f"\\x{self._buffer[y * bytes_per_row + x]:02x}"
            row += "'"
            if y < self._height - 1:
                row += "\\"
            out.append(row)

        out.append("BITMAP = memoryview(_bitmap)")

        with open(directory + filename + ".py", "w") as f:
            f.write("\n".join(out))
