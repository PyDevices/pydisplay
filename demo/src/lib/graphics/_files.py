import struct

from ._framebuf_plus import GS2_HMSB, GS4_HMSB, GS8, MONO_HLSB, RGB565, FrameBuffer


def pbm_to_framebuffer(filename):
    """
    Convert a PBM file to a MONO_HLSB FrameBuffer

    Args:
        filename (str): Filename of the PBM file
    """
    with open(filename, "rb") as f:
        if f.read(3) != b"P4\n":
            raise ValueError(f"Invalid PBM file {filename}")
        data = f.read()  # Read the rest as binary, since MicroPython can't do readline here
    while data[0] == 35:  # Ignore comment lines starting with b'#'
        data = data.split(b"\n", 1)[1]
    dims, data = data.split(b"\n", 1)  # Assumes no comments after dimensions
    width, height = map(int, dims.split())
    buffer = memoryview(bytearray((width + 7) // 8 * height))
    buffer[:] = data
    return FrameBuffer(buffer, width, height, MONO_HLSB)


def pgm_to_framebuffer(filename):
    """
    Convert a PGM file to a GS2_HMSB, GS4_HMSB or GS8 FrameBuffer

    Args:
        filename (str): Filename of the PGM file
    """
    with open(filename, "rb") as f:
        if f.read(3) != b"P5\n":
            raise ValueError(f"Invalid PGM file {filename}")
        data = f.read()  # Read the rest as binary, since MicroPython can't do readline here
    while data[0] == 35:  # Ignore comment lines starting with b'#'
        data = data.split(b"\n", 1)[1]
    dims, data = data.split(b"\n", 1)
    width, height = map(int, dims.split())
    while data[0] == 35:  # Ignore comment lines starting with b'#'
        data = data.split(b"\n", 1)[1]
    max_val_b, data = data.split(b"\n", 1)  # Assumes no comments after max val
    max_value = int(max_val_b)
    if max_value == 3:
        format = GS2_HMSB
        array_size = (width + 3) // 4 * height
    elif max_value == 15:
        format = GS4_HMSB
        array_size = (width + 1) // 2 * height
    elif max_value == 255:
        format = GS8
        array_size = width * height
    else:
        raise ValueError(f"Unsupported max value {max_value}")
    buffer = memoryview(bytearray(array_size))
    buffer[:] = data
    return FrameBuffer(buffer, width, height, format)


def bmp_to_framebuffer(filename):
    """
    Convert a BMP file to a RGB565 FrameBuffer.
    First ensures planes is 1, bits per pixel is 16, and compression is 0.

    Args:
        filename (str): Filename of the
    """
    with open(filename, "rb") as f:
        if f.read(2) != b"BM":
            raise ValueError("Not a BMP file")
        f.seek(10)
        data_offset = struct.unpack("<I", f.read(4))[0]
        f.seek(14)
        width, height = struct.unpack("<II", f.read(8))
        planes = struct.unpack("<H", f.read(2))[0]
        if planes != 1:
            raise ValueError("Invalid BMP file")
        bpp = struct.unpack("<H", f.read(2))[0]
        if bpp != 16:
            raise ValueError("Invalid color depth")
        f.seek(data_offset)
        buffer = memoryview(bytearray(width * height * 2))
        f.seek(54)
        for i in range(height):
            buffer[(height - i - 1) * width * 2 : (height - i) * width * 2] = f.read(width * 2)
    return FrameBuffer(buffer, width, height, RGB565)
