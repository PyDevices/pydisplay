import struct

from ._bmp565 import load_bmp565_buffer, read_bmp565_header, write_bmp565_file
from ._framebuf_plus import GS2_HMSB, GS4_HMSB, GS8, MONO_HLSB, RGB565, FrameBuffer

# Framebuffer formats that ``save_image`` can write, keyed by file extension.
_SAVE_FORMATS = {
    MONO_HLSB: "pbm",
    GS2_HMSB: "pgm",
    GS4_HMSB: "pgm",
    GS8: "pgm",
    RGB565: "bmp",
}


def load_image(filename):
    """Load a ``FrameBuffer`` from a PBM, PGM, or RGB565 BMP file."""
    with open(filename, "rb") as f:
        header = f.read(2)
    if header == b"P4":
        return pbm_to_framebuffer(filename)
    if header == b"P5":
        return pgm_to_framebuffer(filename)
    if header == b"BM":
        return bmp_to_framebuffer(filename)
    raise ValueError(f"Unsupported image file {filename!r} (header {header!r})")


def save_image(fb, filename=None):
    """Save a ``FrameBuffer`` to PBM, PGM, or BMP based on its format.

    MONO_HLSB → PBM, GS2/GS4/GS8 → PGM, RGB565 → BMP. Other formats raise
    ``ValueError``.
    """
    if filename is None:
        filename = "screenshot"
    ext = _SAVE_FORMATS.get(fb.format)
    if ext is None:
        raise ValueError(f"Save not supported for format {fb.format}")
    file_ext = filename.rsplit(".", 1)[-1]
    if file_ext != ext:
        filename += f".{ext}"
    if fb.format == MONO_HLSB:
        with open(filename, "wb") as f:
            f.write(b"P4\n")
            f.write(f"{fb.width} {fb.height}\n".encode())
            f.write(fb.buffer)
    elif fb.format == GS2_HMSB:
        with open(filename, "wb") as f:
            f.write(b"P5\n")
            f.write(f"{fb.width} {fb.height}\n".encode())
            f.write(b"3\n")
            f.write(fb.buffer)
    elif fb.format == GS4_HMSB:
        with open(filename, "wb") as f:
            f.write(b"P5\n")
            f.write(f"{fb.width} {fb.height}\n".encode())
            f.write(b"15\n")
            f.write(fb.buffer)
    elif fb.format == GS8:
        with open(filename, "wb") as f:
            f.write(b"P5\n")
            f.write(f"{fb.width} {fb.height}\n".encode())
            f.write(b"255\n")
            f.write(fb.buffer)
    elif fb.format == RGB565:
        with open(filename, "wb") as f:
            write_bmp565_file(f, fb.buffer, fb.width, fb.height)
    return filename


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
