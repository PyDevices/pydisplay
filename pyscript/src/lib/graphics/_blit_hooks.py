# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Dispatch blit operations to canvas fast paths when available."""

from ._area import Area
from ._capabilities import framebuf_backend

_RGB565_BPP = 2


def clip_blit_bounds(canvas, source, x, y):
    """Return clipped destination/source origin as ``(x0, y0, w, h, src_x, src_y)``.

    Returns ``None`` when the blit is fully outside the canvas.
    """
    if (
        (-x >= source.width)
        or (-y >= source.height)
        or (x >= canvas.width)
        or (y >= canvas.height)
    ):
        return None

    x0 = max(0, x)
    y0 = max(0, y)
    src_x = max(0, -x)
    src_y = max(0, -y)
    w = min(canvas.width, x + source.width) - x0
    h = min(canvas.height, y + source.height) - y0
    return x0, y0, w, h, src_x, src_y


def canvas_accepts_blit_rect(canvas):
    """True when ``canvas.blit_rect`` is a display-style fast path (not RAM copy)."""
    if not callable(getattr(canvas, "blit_rect", None)):
        return False
    from ._framebuf_plus import FrameBuffer

    return not isinstance(canvas, FrameBuffer)


def canvas_accepts_blit_transparent(canvas):
    """True when ``canvas.blit_transparent`` is implemented by the display driver."""
    if not callable(getattr(canvas, "blit_transparent", None)):
        return False
    from ._framebuf_plus import FrameBuffer

    return not isinstance(canvas, FrameBuffer)


def _source_rgb565_bytes_per_pixel(source):
    fmt = getattr(source, "format", None)
    if fmt is None:
        return None
    from ._framebuf_plus import RGB565

    return _RGB565_BPP if fmt == RGB565 else None


def _framebuf_blit_base():
    """Return a real native ``framebuf.FrameBuffer`` base, or ``None`` for the desktop shim."""
    from ._framebuf_plus import FrameBuffer as _GfxFrameBuffer

    try:
        mro = _GfxFrameBuffer.__mro__
    except AttributeError:
        return None
    if len(mro) < 2:
        return None
    base = mro[1]
    if getattr(base, "__module__", "") == "graphics._framebuf":
        return None
    return base


def _can_use_native_framebuffer_blit(canvas, source):
    if framebuf_backend() != "native":
        return False
    if not (
        hasattr(canvas, "buffer")
        and hasattr(source, "buffer")
        and hasattr(canvas, "format")
        and hasattr(source, "format")
    ):
        return False
    from ._framebuf_plus import FrameBuffer

    if not (isinstance(canvas, FrameBuffer) and isinstance(source, FrameBuffer)):
        return False
    return _framebuf_blit_base() is not None


def _native_framebuffer_blit(canvas, source, x, y, key=-1, palette=None):
    """Call the underlying ``framebuf.FrameBuffer.blit`` (C on MCU)."""
    base = _framebuf_blit_base()
    if base is None:
        raise RuntimeError("native framebuffer blit unavailable")
    base.blit(canvas, source, x, y, key, palette)


def _pure_framebuffer_blit(canvas, source, x, y, key=-1, palette=None):
    """Blit between pure-Python FrameBuffers without re-entering ``_shapes.blit``."""
    clipped = clip_blit_bounds(canvas, source, x, y)
    if clipped is None:
        return None

    x0, y0, w, h, src_x, src_y = clipped
    src_fmt = source._format
    dst_fmt = canvas._format
    pal_fmt = palette._format if palette is not None else None

    for row in range(h):
        sy = src_y + row
        dy = y0 + row
        for col in range(w):
            sx = src_x + col
            dx = x0 + col
            color = src_fmt.get_pixel(source, sx, sy)
            if pal_fmt is not None:
                color = pal_fmt.get_pixel(palette, color, 0)
            if color != key:
                dst_fmt.set_pixel(canvas, dx, dy, color)
    return Area(x0, y0, w, h)


def _extract_rgb565_rows(source, src_x, src_y, w, h):
    bpp = _RGB565_BPP
    row_bytes = w * bpp
    out = bytearray(row_bytes * h)
    for row in range(h):
        src_start = ((src_y + row) * source.width + src_x) * bpp
        src_end = src_start + row_bytes
        dst_start = row * row_bytes
        out[dst_start : dst_start + row_bytes] = source.buffer[src_start:src_end]
    return out


def blit_rect_to_buffer(canvas, buf, x, y, w, h, *, bpp=_RGB565_BPP):
    """Copy an RGB565 rectangle into ``canvas.buffer``."""
    if x < 0 or y < 0 or x + w > canvas.width or y + h > canvas.height:
        raise ValueError("The provided x, y, w, h values are out of range")

    expected = w * h * bpp
    if len(buf) != expected:
        raise ValueError(
            f"The source buffer is not the correct size (got {len(buf)} bytes, expected {expected})"
        )

    for row in range(h):
        source_begin = row * w * bpp
        source_end = source_begin + w * bpp
        dest_begin = ((y + row) * canvas.width + x) * bpp
        dest_end = dest_begin + w * bpp
        canvas.buffer[dest_begin:dest_end] = buf[source_begin:source_end]


def blit_rect_dispatch(canvas, buf, x, y, w, h):
    """Blit a raw RGB565 buffer, using a canvas hook when available."""
    if canvas_accepts_blit_rect(canvas):
        canvas.blit_rect(buf, x, y, w, h)
    else:
        blit_rect_to_buffer(canvas, buf, x, y, w, h)
    return Area(x, y, w, h)


def try_fast_framebuffer_blit(canvas, source, x, y, key=-1, palette=None):
    """Framebuffer blit via native or ``blit_rect`` fast paths.

    Returns an :class:`Area` on success, or ``None`` to use the pixel loop.
    """
    clipped = clip_blit_bounds(canvas, source, x, y)
    if clipped is None:
        return None

    x0, y0, w, h, src_x, src_y = clipped

    if _can_use_native_framebuffer_blit(canvas, source):
        _native_framebuffer_blit(canvas, source, x, y, key, palette)
        return Area(x0, y0, w, h)

    from ._framebuf_plus import FrameBuffer

    if (
        isinstance(canvas, FrameBuffer)
        and isinstance(source, FrameBuffer)
        and hasattr(canvas, "_format")
        and hasattr(source, "_format")
        and _framebuf_blit_base() is None
    ):
        pure = _pure_framebuffer_blit(canvas, source, x, y, key, palette)
        if pure is not None:
            return pure

    if key != -1 or palette is not None:
        return None

    if _source_rgb565_bytes_per_pixel(source) is None or not hasattr(source, "buffer"):
        return None

    data = _extract_rgb565_rows(source, src_x, src_y, w, h)
    blit_rect_dispatch(canvas, data, x0, y0, w, h)
    return Area(x0, y0, w, h)
