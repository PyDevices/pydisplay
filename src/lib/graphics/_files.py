import struct

from ._bmp565 import load_bmp565_buffer, read_bmp565_header
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
    Convert an RGB565 BMP file to a FrameBuffer.

    Args:
        filename (str): Path to the BMP file.
    """
    with open(filename, "rb") as f:
        width, height, data_offset = read_bmp565_header(f)
        buffer = load_bmp565_buffer(f, width, height, data_offset)
    return FrameBuffer(buffer, width, height, RGB565)
