# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
A class to read a 16-bit RGB565 BMP file and present it as a sliceable object.

Usage:
    bmp = BMP565('image.bmp')
    print(bmp.width, bmp.height, self.bpp)
    print(bmp[0])  # Get pixel color at 0 as an integer
    print(bmp[0, 0])  # Get pixel color at (0, 0) as an integer
    print(bmp[0:10])  # Get the first 10 lines as a memoryview object
    print(bmp[0:10, 0:10])  # Get a 10x10 slice of the image as a bytearray object
"""

import os
import struct


class BMP565:
    def __init__(
        self, filename=None, source=None, streamed=False, mirrored=False, width=None, height=None
    ):
        self._filename = filename
        self._streamed = streamed
        self._mirrored = mirrored
        self._buffer = None
        self._mv = None
        if source is not None:
            self.width = width
            self.height = height
            self._buffer = source
        elif filename is not None:
            if self._streamed is True:
                self._file = open(filename, "rb")  # noqa: SIM115  # kept open for streaming reads
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
            # if the file already exists, add a number to the filename
            filename, ext = filename.split(".")
            # if the filename already has a number, increment it
            if filename[-1].isdigit():
                # strip the number off the end of the filename and save it so we can increment it
                ver = ""
                while filename[-1].isdigit():
                    ver = filename[-1] + ver
                    filename = filename[:-1]
                filename += str(int(ver) + 1) + "." + ext
            else:
                filename += "_1." + ext
        with open(filename, "wb") as f:
            f.write(b"BM")  # Offset 0: Signature
            f.write(struct.pack("<I", 14 + 40 + len(self._buffer)))  # Offset 2: File size
            f.write(b"\x00\x00\x00\x00")  # Offset 6: Unused
            f.write(struct.pack("<I", 14 + 40))  # Offset 10: Data offset
            # Windows BITMAPINFOHEADER
            f.write(struct.pack("<I", 40))  # Offset 14: Header size
            f.write(struct.pack("<II", self.width, self.height))  # Offset 18: Width, Height
            f.write(struct.pack("<H", 1))  # Offset 26: Planes
            f.write(struct.pack("<H", 16))  # Offset 28: Bits per pixel
            f.write(b"\x00\x00\x00\x00")  # Offset 30: Compression
            f.write(struct.pack("<I", len(self._buffer)))  # Offset 34: Image size
            f.write(b"\x00\x00\x00\x00")  # Offset 38: X pixels per meter
            f.write(b"\x00\x00\x00\x00")  # Offset 42: Y pixels per meter
            f.write(b"\x00\x00\x00\x00")  # Offset 46: Colors in color table
            f.write(b"\x00\x00\x00\x00")  # Offset 50: Important color count
            # The order of the lines is reversed when reading the file or buffer.  We need to reverse it back.
            for i in range(self.height):
                f.write(
                    self._buffer[
                        (self.height - i - 1) * self.width * 2 : (self.height - i) * self.width * 2
                    ]
                )
        return filename

    def _read_header(self, f):
        if f.read(2) != b"BM":
            raise ValueError("Not a BMP file")
        file_size = struct.unpack("<I", f.read(4))[0]  # noqa: F841
        f.seek(10)
        self.data_offset = struct.unpack("<I", f.read(4))[0]
        header_size = struct.unpack("<I", f.read(4))[0]  # noqa: F841
        self.width, self.height = struct.unpack("<II", f.read(8))
        planes = struct.unpack("<H", f.read(2))[0]
        if planes != 1:
            raise ValueError("Invalid BMP file")
        self.bpp = struct.unpack("<H", f.read(2))[0]
        if self.bpp != 16:
            raise ValueError("Invalid color depth")
        self.BPP = self.bpp // 8

    def _read_data(self, f):
        # BMP files are stored from bottom up
        # We need to reverse the data without reversing the color byte pairs
        # by reading one row at a time and adding that row to the beginning of the data
        self._buffer = bytearray()
        for i in range(self.height):
            f.seek(self.data_offset + (self.height - i - 1) * self.width * 2)
            self._buffer += f.read(self.width * 2)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            # Called as bmp[x, y]
            x, y = key
            if isinstance(x, slice) and isinstance(y, slice):
                # Called as bmp[0:10, 0:10].  Return a 10x10 slice of the image
                xstart = x.start if x.start is not None else 0
                xstop = x.stop if x.stop is not None else self.width
                ystart = y.start if y.start is not None else 0
                ystop = y.stop if y.stop is not None else self.height
                data = bytearray()
                for i in range(ystart, ystop):
                    data += self._get((i * self.width + xstart), (i * self.width + xstop))
                return data
            elif isinstance(x, int) and isinstance(y, int):
                # Called as bmp[0, 0].  Return the color of the pixel at (0, 0)
                return struct.unpack(
                    "<H", self._get((y * self.width + x), (y * self.width + x) + 1)
                )[0]
            else:
                raise ValueError("Invalid key")
        elif isinstance(key, int):
            # Called as bmp[0].  Return the color of the pixel at index 0
            return struct.unpack("<H", self._get(key, key + 1))[0]
        elif isinstance(key, slice):
            # Called as bmp[i:j].  Return lines i through j
            start = key.start if key.start is not None else 0
            stop = key.stop if key.stop is not None else self.height
            return self[0 : self.width, start:stop]
        else:
            raise ValueError("Invalid key")

    def _get(self, start, stop):
        # start and stop are pixel indices, not byte indices
        if not self._streamed:
            return self._mv[start * self.BPP : stop * self.BPP]
        else:
            # BMP files are stored from bottom up.
            # We need to translate the slice to the correct position in the file.
            length = stop - start
            start_row, start_col = divmod(start, self.width)
            begin = (self.height - start_row - 1) * self.width + start_col
            self._file.seek(self.data_offset + begin * self.BPP)
            if not self._mirrored:
                return self._file.read(length * self.BPP)
            else:
                # Micropython's slice notation doesn't support negative indices
                # so we need to read the entire row and reorder the bytes
                pixels = []
                for _i in range(length):
                    pixels.insert(0, self._file.read(self.BPP))
                return b"".join(pixels)

    def deinit(self):
        if self._streamed:
            self._file.close()

    def __exit__(self, exception_type, exception_value, traceback):
        self.deinit()

    def __del__(self):
        self.deinit()

    def __enter__(self):
        self.__init__()
        return self

    def __len__(self):
        return self.width * self.height * self.BPP
