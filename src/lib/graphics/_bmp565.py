# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""RGB565 Windows BMP read/write helpers and sliceable BMP565 asset."""

import os
import struct

BMP565_BPP = 16
BMP565_BYTES_PER_PIXEL = 2


def read_bmp565_header(f):
    """Read an RGB565 BMP header from an open binary file.

    Returns:
        tuple[int, int, int]: width, height, data_offset
    """
    if f.read(2) != b"BM":
        raise ValueError("Not a BMP file")
    f.seek(10)
    data_offset = struct.unpack("<I", f.read(4))[0]
    f.seek(14)
    _header_size = struct.unpack("<I", f.read(4))[0]
    width, height = struct.unpack("<II", f.read(8))
    planes = struct.unpack("<H", f.read(2))[0]
    if planes != 1:
        raise ValueError("Invalid BMP file")
    bpp = struct.unpack("<H", f.read(2))[0]
    if bpp != BMP565_BPP:
        raise ValueError("Invalid color depth")
    return width, height, data_offset


def load_bmp565_buffer(f, width, height, data_offset):
    """Load BMP pixel rows into a top-down RGB565 buffer."""
    row_bytes = width * BMP565_BYTES_PER_PIXEL
    buffer = bytearray(row_bytes * height)
    for row in range(height):
        f.seek(data_offset + (height - row - 1) * row_bytes)
        chunk = f.read(row_bytes)
        if len(chunk) != row_bytes:
            raise ValueError("Truncated BMP image data")
        start = row * row_bytes
        buffer[start : start + row_bytes] = chunk
    return buffer


def write_bmp565_header(f, width, height, data_size):
    """Write the Windows BITMAPINFOHEADER for an RGB565 image."""
    f.write(b"BM")
    f.write(struct.pack("<I", 14 + 40 + data_size))
    f.write(b"\x00\x00\x00\x00")
    f.write(struct.pack("<I", 14 + 40))
    f.write(struct.pack("<I", 40))
    f.write(struct.pack("<II", width, height))
    f.write(struct.pack("<H", 1))
    f.write(struct.pack("<H", BMP565_BPP))
    f.write(b"\x00\x00\x00\x00")
    f.write(struct.pack("<I", data_size))
    f.write(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")


def write_bmp565_rows(f, buffer, width, height):
    """Write pixel rows bottom-up (BMP on-disk order)."""
    row_bytes = width * BMP565_BYTES_PER_PIXEL
    for row in range(height):
        start = (height - row - 1) * row_bytes
        f.write(buffer[start : start + row_bytes])


def write_bmp565_file(f, buffer, width, height):
    """Write a complete RGB565 BMP file."""
    data_size = width * height * BMP565_BYTES_PER_PIXEL
    write_bmp565_header(f, width, height, data_size)
    write_bmp565_rows(f, buffer, width, height)


class BMP565:
    """Read a 16-bit RGB565 BMP as a sliceable, optionally streamed asset."""

    def __init__(
        self, filename=None, source=None, streamed=False, mirrored=False, width=None, height=None
    ):
        self._filename = filename
        self._streamed = streamed
        self._mirrored = mirrored
        self._buffer = None
        self._mv = None
        self._file = None
        if source is not None:
            self.width = width
            self.height = height
            self.bpp = BMP565_BPP
            self.BPP = BMP565_BYTES_PER_PIXEL
            self._buffer = source
        elif filename is not None:
            if self._streamed:
                self._file = open(filename, "rb")  # noqa: SIM115
                self._read_header(self._file)
            else:
                with open(filename, "rb") as f:
                    self._read_header(f)
                    self._read_data(f)
        else:
            raise ValueError("Invalid arguments")

        if self._buffer is not None:
            self._mv = memoryview(self._buffer)

    def __call__(self, x, y, w, h):
        return self[x : x + w, y : y + h]

    @property
    def buffer(self):
        return self._mv

    @staticmethod
    def _exists(filename):
        try:
            os.stat(filename)
            return True
        except OSError:
            return False

    def save(self, filename=None):
        if filename is None:
            filename = self._filename if self._filename is not None else "image.bmp"
        while self._exists(filename):
            filename, ext = filename.split(".")
            if filename[-1].isdigit():
                ver = ""
                while filename[-1].isdigit():
                    ver = filename[-1] + ver
                    filename = filename[:-1]
                filename += str(int(ver) + 1) + "." + ext
            else:
                filename += "_1." + ext
        with open(filename, "wb") as f:
            write_bmp565_file(f, self._buffer, self.width, self.height)
        return filename

    def _read_header(self, f):
        self.width, self.height, self.data_offset = read_bmp565_header(f)
        self.bpp = BMP565_BPP
        self.BPP = BMP565_BYTES_PER_PIXEL

    def _read_data(self, f):
        self._buffer = load_bmp565_buffer(f, self.width, self.height, self.data_offset)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            x, y = key
            if isinstance(x, slice) and isinstance(y, slice):
                xstart = x.start if x.start is not None else 0
                xstop = x.stop if x.stop is not None else self.width
                ystart = y.start if y.start is not None else 0
                ystop = y.stop if y.stop is not None else self.height
                data = bytearray()
                for i in range(ystart, ystop):
                    data += self._get((i * self.width + xstart), (i * self.width + xstop))
                return data
            if isinstance(x, int) and isinstance(y, int):
                return struct.unpack(
                    "<H", self._get((y * self.width + x), (y * self.width + x) + 1)
                )[0]
            raise ValueError("Invalid key")
        if isinstance(key, int):
            return struct.unpack("<H", self._get(key, key + 1))[0]
        if isinstance(key, slice):
            start = key.start if key.start is not None else 0
            stop = key.stop if key.stop is not None else self.height
            return self[0 : self.width, start:stop]
        raise ValueError("Invalid key")

    def _get(self, start, stop):
        if not self._streamed:
            return self._mv[start * self.BPP : stop * self.BPP]
        length = stop - start
        start_row, start_col = divmod(start, self.width)
        begin = (self.height - start_row - 1) * self.width + start_col
        self._file.seek(self.data_offset + begin * self.BPP)
        if not self._mirrored:
            return self._file.read(length * self.BPP)
        pixels = []
        for _ in range(length):
            pixels.insert(0, self._file.read(self.BPP))
        return b"".join(pixels)

    def deinit(self):
        if self._streamed and self._file is not None:
            self._file.close()
            self._file = None

    def __exit__(self, exception_type, exception_value, traceback):
        self.deinit()

    def __del__(self):
        self.deinit()
