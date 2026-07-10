#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Compare MicroPython's built-in ``framebuf`` C module to ``add_ons/framebuf.py``.

Run on MicroPython only (native ``framebuf`` must be the C extmod)::

    cd /path/to/pydisplay
    micropython tools/compare_framebuf_mp.py
    micropython.exe tools/compare_framebuf_mp.py

The C module owns the name ``framebuf``, so the Python implementation is loaded
via ``exec`` from ``src/add_ons/framebuf.py``. Constants and buffer behaviour
are compared side by side; mismatches print and exit 1.
"""

import sys


def _dirname(path):
    i = path.rfind("/")
    if i < 0:
        return "."
    if i == 0:
        return "/"
    return path[:i]


def _find_framebuf_py():
    p = _dirname(sys.argv[0])
    for _ in range(6):
        candidate = p + "/src/add_ons/framebuf.py"
        if _file_exists(candidate):
            return candidate
        p = _dirname(p)
    return None


def _file_exists(path):
    try:
        with open(path):
            pass
        return True
    except OSError:
        return False


def _load_python_framebuf(path):
    ns = {"__name__": "framebuf_py"}
    with open(path) as f:
        exec(f.read(), ns)
    return ns


def _fail(errors, msg):
    errors.append(msg)
    print("FAIL:", msg)


def _ok(label):
    print("ok:", label)


def _compare_buffers(errors, label, nbuf, pbuf, length):
    nb = bytes(nbuf[:length])
    pb = bytes(pbuf[:length])
    if nb != pb:
        diff = 0
        for a, b in zip(nb, pb):
            if a != b:
                diff += 1
        _fail(errors, "{}: buffer mismatch ({} bytes differ)".format(label, diff))
        return
    _ok(label)


def _compare_pixels(errors, label, fb_n, fb_p, points):
    for x, y in points:
        nv = fb_n.pixel(x, y)
        pv = fb_p.pixel(x, y)
        if nv != pv:
            _fail(errors, "{}: pixel({}, {}) native={} python={}".format(label, x, y, nv, pv))
            return
    _ok(label + " pixels")


def _rgb565_buf(w, h):
    return bytearray(w * h * 2 + 16)


def _mono_buf(w, h):
    return bytearray((w * h + 7) // 8 + 16)


def main():
    if sys.implementation.name != "micropython":
        print(
            "compare_framebuf_mp.py requires MicroPython (built-in C framebuf).", file=sys.stderr
        )
        return 1

    try:
        import framebuf as native
    except ImportError:
        print(
            "compare_framebuf_mp.py requires MicroPython with the built-in C framebuf module.",
            file=sys.stderr,
        )
        return 1

    py_path = _find_framebuf_py()
    if not py_path:
        print(
            "missing canonical module: src/add_ons/framebuf.py (run from repo root)",
            file=sys.stderr,
        )
        return 1

    py = _load_python_framebuf(py_path)
    PyFB = py["FrameBuffer"]
    errors = []

    const_names = (
        "MONO_VLSB",
        "MONO_HLSB",
        "MONO_HMSB",
        "RGB565",
        "GS2_HMSB",
        "GS4_HMSB",
        "GS8",
        "MVLSB",
    )
    for name in const_names:
        nv = getattr(native, name, None)
        pv = py.get(name, None)
        if nv != pv:
            _fail(errors, "constant {}: native={} python={}".format(name, nv, pv))
        else:
            _ok("constant " + name)

    # --- RGB565 scenarios ---
    w, h = 16, 16
    nbuf = _rgb565_buf(w, h)
    pbuf = _rgb565_buf(w, h)
    fb_n = native.FrameBuffer(nbuf, w, h, native.RGB565)
    fb_p = PyFB(pbuf, w, h, py["RGB565"])

    fb_n.fill(0xF800)
    fb_p.fill(0xF800)
    _compare_buffers(errors, "RGB565 fill", nbuf, pbuf, w * h * 2)

    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.pixel(3, 4, 0xBEEF)
    fb_p.pixel(3, 4, 0xBEEF)
    _compare_pixels(errors, "RGB565 pixel", fb_n, fb_p, ((3, 4), (0, 0)))

    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.fill_rect(2, 2, 5, 5, 0x07E0)
    fb_p.fill_rect(2, 2, 5, 5, 0x07E0)
    _compare_buffers(errors, "RGB565 fill_rect", nbuf, pbuf, w * h * 2)

    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.hline(1, 3, 8, 0x1234)
    fb_p.hline(1, 3, 8, 0x1234)
    _compare_buffers(errors, "RGB565 hline", nbuf, pbuf, w * h * 2)

    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.line(0, 0, 10, 10, 0x00FF)
    fb_p.line(0, 0, 10, 10, 0x00FF)
    _compare_buffers(errors, "RGB565 line", nbuf, pbuf, w * h * 2)

    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.rect(4, 4, 6, 6, 0xFFFF)
    fb_p.rect(4, 4, 6, 6, 0xFFFF)
    _compare_buffers(errors, "RGB565 rect outline", nbuf, pbuf, w * h * 2)

    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.ellipse(8, 8, 4, 4, 0xF81F)
    fb_p.ellipse(8, 8, 4, 4, 0xF81F)
    _compare_buffers(errors, "RGB565 ellipse", nbuf, pbuf, w * h * 2)

    fb_n.fill(0)
    fb_p.fill(0)
    import array

    pts = array.array("h", [2, 2, 12, 2, 12, 10, 2, 10])
    fb_n.poly(0, 0, pts, 0x8410)
    fb_p.poly(0, 0, pts, 0x8410)
    _compare_buffers(errors, "RGB565 poly", nbuf, pbuf, w * h * 2)

    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.text("A", 1, 1, 1)
    fb_p.text("A", 1, 1, 1)
    _compare_buffers(errors, "RGB565 text", nbuf, pbuf, w * h * 2)

    # blit with key
    sw, sh = 8, 8
    s_nbuf = _rgb565_buf(sw, sh)
    s_pbuf = _rgb565_buf(sw, sh)
    src_n = native.FrameBuffer(s_nbuf, sw, sh, native.RGB565)
    src_p = PyFB(s_pbuf, sw, sh, py["RGB565"])
    src_n.fill(0)
    src_p.fill(0)
    src_n.fill_rect(0, 0, 4, 4, 0xFFFF)
    src_p.fill_rect(0, 0, 4, 4, 0xFFFF)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.blit(src_n, 2, 3)
    fb_p.blit(src_p, 2, 3)
    _compare_buffers(errors, "RGB565 blit", nbuf, pbuf, w * h * 2)

    # scroll (byte-aligned depth)
    fb_n.fill(0x1234)
    fb_p.fill(0x1234)
    fb_n.pixel(0, 0, 0xABCD)
    fb_p.pixel(0, 0, 0xABCD)
    fb_n.scroll(2, 1)
    fb_p.scroll(2, 1)
    _compare_buffers(errors, "RGB565 scroll", nbuf, pbuf, w * h * 2)

    # --- MONO_HLSB spot check ---
    mw, mh = 16, 16
    mnbuf = _mono_buf(mw, mh)
    mpbuf = _mono_buf(mw, mh)
    m_n = native.FrameBuffer(mnbuf, mw, mh, native.MONO_HLSB)
    m_p = PyFB(mpbuf, mw, mh, py["MONO_HLSB"])
    m_n.fill(1)
    m_p.fill(1)
    m_n.fill_rect(2, 2, 4, 4, 0)
    m_p.fill_rect(2, 2, 4, 4, 0)
    _compare_pixels(
        errors,
        "MONO_HLSB fill_rect",
        m_n,
        m_p,
        ((0, 0), (2, 2), (3, 3), (5, 5), (15, 15)),
    )

    print()
    if errors:
        print("{} mismatch(es).".format(len(errors)))
        return 1
    print("All checks passed (native C framebuf vs add_ons/framebuf.py).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130) from None
