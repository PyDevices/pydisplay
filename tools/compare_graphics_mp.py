#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Compare native ``graphics`` cmod to ``src/lib/graphics`` on MicroPython.

Run on MicroPython with the graphics C usermod linked (``~/bin/micropython``)::

    cd /path/to/pydisplay
    micropython tools/compare_graphics_mp.py

The built-in ``graphics`` module is the C implementation. The pure-Python tree is
staged as ``graphics_py`` under ``.cursor/compare_graphics_py/`` (gitignored) so
both can coexist. Constants, ``Area`` geometry, ``FrameBuffer`` buffer bytes,
module-level draw helpers, and font helpers are compared side by side.
"""

import sys

_GRAPHICS_PY_FILES = (
    "__init__.py",
    "_area.py",
    "_clip.py",
    "_blit_hooks.py",
    "_framebuf_plus.py",
    "_shapes.py",
    "_font.py",
    "_font_8x8.py",
    "_font_8x14.py",
    "_font_8x16.py",
    "_draw.py",
    "_bmp565.py",
    "_files.py",
)

_PYDISPLAY_ALL = (
    "BMP565",
    "GS2_HMSB",
    "GS4_HMSB",
    "GS8",
    "MONO_HLSB",
    "MONO_HMSB",
    "MONO_VLSB",
    "RGB565",
    "Area",
    "Draw",
    "Font",
    "FrameBuffer",
    "arc",
    "blit",
    "blit_rect",
    "blit_transparent",
    "bmp_to_framebuffer",
    "circle",
    "ellipse",
    "fill",
    "fill_rect",
    "gradient_rect",
    "hline",
    "implementation",
    "line",
    "load_image",
    "pbm_to_framebuffer",
    "pgm_to_framebuffer",
    "pixel",
    "poly",
    "polygon",
    "rect",
    "round_rect",
    "save_image",
    "text",
    "text8",
    "text14",
    "text16",
    "triangle",
    "vline",
)

_FORMAT_CONSTS = (
    "MONO_VLSB",
    "MONO_HLSB",
    "MONO_HMSB",
    "RGB565",
    "GS2_HMSB",
    "GS4_HMSB",
    "GS8",
    "RGB888",
)


def _dirname(path):
    i = path.rfind("/")
    if i < 0:
        return "."
    if i == 0:
        return "/"
    return path[:i]


def _file_exists(path):
    try:
        with open(path):
            pass
        return True
    except OSError:
        return False


def _find_repo_root():
    p = _dirname(sys.argv[0])
    for _ in range(6):
        if _file_exists(p + "/src/add_ons/framebuf.py"):
            return p
        p = _dirname(p)
    return None


def _makedirs(path):
    if not path or path == ".":
        return
    parts = [part for part in path.split("/") if part]
    cur = ""
    import os

    for part in parts:
        cur = cur + "/" + part if cur else part
        try:
            os.mkdir(cur)
        except OSError:
            pass


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


def _compare_value(errors, label, native_val, py_val):
    if native_val != py_val:
        _fail(errors, "{}: native={!r} python={!r}".format(label, native_val, py_val))
        return
    _ok(label)


def _rgb565_buf(w, h):
    return bytearray(w * h * 2 + 16)


def _mono_buf(w, h):
    return bytearray((w * h + 7) // 8 + 16)


def _paired_rgb565(native, py, w, h):
    nbuf = _rgb565_buf(w, h)
    pbuf = _rgb565_buf(w, h)
    fb_n = native.FrameBuffer(nbuf, w, h, native.RGB565)
    fb_p = py.FrameBuffer(pbuf, w, h, py.RGB565)
    return fb_n, fb_p, nbuf, pbuf


def _stage_python_graphics(repo):
    import os

    src = repo + "/src/lib/graphics"
    staging = repo + "/.cursor/compare_graphics_py"
    pkg_dir = staging + "/graphics_py"
    _makedirs(pkg_dir)

    framebuf_src = repo + "/src/add_ons/framebuf.py"
    with open(framebuf_src) as f:
        framebuf_code = f.read()
    with open(pkg_dir + "/framebuf.py", "w") as f:
        f.write(framebuf_code)

    for name in _GRAPHICS_PY_FILES:
        with open(src + "/" + name) as f:
            code = f.read()
        with open(pkg_dir + "/" + name, "w") as f:
            f.write(code)

    for key in list(sys.modules):
        if key == "graphics_py" or key.startswith("graphics_py."):
            del sys.modules[key]

    if staging not in sys.path:
        sys.path.insert(0, staging)

    import graphics_py

    return graphics_py


def _check_exports(errors, native, py):
    if native.implementation() != "native_cmod":
        _fail(errors, "native implementation: {!r}".format(native.implementation()))
    else:
        _ok("native implementation")

    if py.implementation() != "pydisplay_python":
        _fail(errors, "python implementation: {!r}".format(py.implementation()))
    else:
        _ok("python implementation")

    for name in _PYDISPLAY_ALL:
        if not hasattr(native, name):
            _fail(errors, "native missing export: " + name)
        elif not hasattr(py, name):
            _fail(errors, "python missing export: " + name)
        else:
            _ok("export " + name)


def _check_constants(errors, native, py):
    for name in _FORMAT_CONSTS:
        nv = getattr(native, name, None)
        pv = getattr(py, name, None)
        if nv != pv:
            _fail(errors, "constant {}: native={} python={}".format(name, nv, pv))
        else:
            _ok("constant " + name)


def _check_area(errors, native, py):
    a_n = native.Area(0, 0, 10, 10)
    a_p = py.Area(0, 0, 10, 10)
    _compare_value(errors, "Area contains", a_n.contains(5, 5), a_p.contains(5, 5))
    _compare_value(errors, "Area half-open edge", a_n.contains(10, 10), a_p.contains(10, 10))
    _compare_value(
        errors,
        "Area intersects",
        native.Area(0, 0, 5, 5).intersects(native.Area(4, 4, 5, 5)),
        py.Area(0, 0, 5, 5).intersects(py.Area(4, 4, 5, 5)),
    )
    _compare_value(
        errors,
        "Area union",
        native.Area(0, 0, 2, 2) + native.Area(4, 4, 2, 2),
        py.Area(0, 0, 2, 2) + py.Area(4, 4, 2, 2),
    )
    _compare_value(errors, "Area repr", repr(a_n), repr(a_p))


def _check_framebuffer_ops(errors, native, py):
    w, h = 16, 16
    length = w * h * 2

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0xF800)
    fb_p.fill(0xF800)
    _compare_buffers(errors, "FrameBuffer fill", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.pixel(3, 4, 0xBEEF)
    fb_p.pixel(3, 4, 0xBEEF)
    _compare_buffers(errors, "FrameBuffer pixel", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.fill_rect(2, 2, 5, 5, 0x07E0)
    fb_p.fill_rect(2, 2, 5, 5, 0x07E0)
    _compare_buffers(errors, "FrameBuffer fill_rect", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.hline(1, 3, 8, 0x1234)
    fb_p.hline(1, 3, 8, 0x1234)
    _compare_buffers(errors, "FrameBuffer hline", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.line(0, 0, 10, 10, 0x00FF)
    fb_p.line(0, 0, 10, 10, 0x00FF)
    _compare_buffers(errors, "FrameBuffer line", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.rect(4, 4, 6, 6, 0xFFFF)
    fb_p.rect(4, 4, 6, 6, 0xFFFF)
    _compare_buffers(errors, "FrameBuffer rect", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.ellipse(8, 8, 4, 4, 0xF81F)
    fb_p.ellipse(8, 8, 4, 4, 0xF81F)
    _compare_buffers(errors, "FrameBuffer ellipse", nbuf, pbuf, length)

    import array

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    pts = array.array("h", [2, 2, 12, 2, 12, 10, 2, 10])
    fb_n.poly(0, 0, pts, 0x8410)
    fb_p.poly(0, 0, pts, 0x8410)
    _compare_buffers(errors, "FrameBuffer poly", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.text("A", 1, 1, 1)
    fb_p.text("A", 1, 1, 1)
    _compare_buffers(errors, "FrameBuffer text", nbuf, pbuf, length)

    sw, sh = 8, 8
    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    s_nbuf = _rgb565_buf(sw, sh)
    s_pbuf = _rgb565_buf(sw, sh)
    src_n = native.FrameBuffer(s_nbuf, sw, sh, native.RGB565)
    src_p = py.FrameBuffer(s_pbuf, sw, sh, py.RGB565)
    src_n.fill_rect(0, 0, 4, 4, 0xFFFF)
    src_p.fill_rect(0, 0, 4, 4, 0xFFFF)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.blit(src_n, 2, 3)
    fb_p.blit(src_p, 2, 3)
    _compare_buffers(errors, "FrameBuffer blit", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0x1234)
    fb_p.fill(0x1234)
    fb_n.pixel(0, 0, 0xABCD)
    fb_p.pixel(0, 0, 0xABCD)
    fb_n.scroll(2, 1)
    fb_p.scroll(2, 1)
    _compare_buffers(errors, "FrameBuffer scroll", nbuf, pbuf, length)


def _check_module_shapes(errors, native, py):
    w, h = 32, 32
    length = w * h * 2

    def run(label, draw):
        fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
        draw(native, py, fb_n, fb_p)
        _compare_buffers(errors, label, nbuf, pbuf, length)

    run(
        "fill_rect()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.fill_rect(fn, 2, 2, 8, 8, 0xF800),
            p.fill_rect(fp, 2, 2, 8, 8, 0xF800),
        ),
    )
    run(
        "line()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.line(fn, 0, 0, 20, 20, 0x07E0),
            p.line(fp, 0, 0, 20, 20, 0x07E0),
        ),
    )
    run(
        "hline()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.hline(fn, 1, 4, 12, 0x1234),
            p.hline(fp, 1, 4, 12, 0x1234),
        ),
    )
    run(
        "vline()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.vline(fn, 3, 2, 10, 0x4321),
            p.vline(fp, 3, 2, 10, 0x4321),
        ),
    )
    run(
        "rect()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.rect(fn, 4, 4, 10, 8, 0xFFFF),
            p.rect(fp, 4, 4, 10, 8, 0xFFFF),
        ),
    )
    run(
        "ellipse()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.ellipse(fn, 16, 16, 8, 5, 0xF81F),
            p.ellipse(fp, 16, 16, 8, 5, 0xF81F),
        ),
    )
    run(
        "circle()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.circle(fn, 16, 16, 8, 0x8410),
            p.circle(fp, 16, 16, 8, 0x8410),
        ),
    )
    run(
        "pixel()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.pixel(fn, 5, 6, 0xBEEF),
            p.pixel(fp, 5, 6, 0xBEEF),
        ),
    )
    run(
        "triangle()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.triangle(fn, 4, 4, 20, 6, 10, 24, 0x07FF),
            p.triangle(fp, 4, 4, 20, 6, 10, 24, 0x07FF),
        ),
    )


def _check_fonts(errors, native, py):
    w, h = 48, 48
    length = w * h * 2

    def run(label, draw):
        fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
        draw(native, py, fb_n, fb_p)
        _compare_buffers(errors, label, nbuf, pbuf, length)

    run(
        "text8()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.text8(fn, "Hi", 0, 0, 0xFFFF),
            p.text8(fp, "Hi", 0, 0, 0xFFFF),
        ),
    )
    run(
        "text()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.text(fn, "A", 0, 0, 1),
            p.text(fp, "A", 0, 0, 1),
        ),
    )
    run(
        "text14()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.text14(fn, "A", 0, 0, 0xFFFF),
            p.text14(fp, "A", 0, 0, 0xFFFF),
        ),
    )
    run(
        "text16()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.text16(fn, "A", 0, 0, 0xFFFF),
            p.text16(fp, "A", 0, 0, 0xFFFF),
        ),
    )


def _check_draw(errors, native, py):
    w, h = 32, 32
    length = w * h * 2
    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    native.Draw(fb_n).fill_rect(1, 1, 6, 6, 0x1234)
    py.Draw(fb_p).fill_rect(1, 1, 6, 6, 0x1234)
    _compare_buffers(errors, "Draw.fill_rect", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    native.Draw(fb_n).line(0, 0, 15, 15, 0x07E0)
    py.Draw(fb_p).line(0, 0, 15, 15, 0x07E0)
    _compare_buffers(errors, "Draw.line", nbuf, pbuf, length)


def main():
    if sys.implementation.name != "micropython":
        print("compare_graphics_mp.py requires MicroPython.", file=sys.stderr)
        return 1

    try:
        import graphics as native
    except ImportError:
        print(
            "compare_graphics_mp.py requires MicroPython with the graphics C usermod.",
            file=sys.stderr,
        )
        return 1

    repo = _find_repo_root()
    if not repo:
        print("missing repo root (expected src/add_ons/framebuf.py)", file=sys.stderr)
        return 1

    try:
        py = _stage_python_graphics(repo)
    except OSError as e:
        print("failed to stage python graphics:", e, file=sys.stderr)
        return 1

    errors = []

    _check_exports(errors, native, py)
    _check_constants(errors, native, py)
    _check_area(errors, native, py)
    _check_framebuffer_ops(errors, native, py)
    _check_module_shapes(errors, native, py)
    _check_draw(errors, native, py)
    _check_fonts(errors, native, py)

    print()
    if errors:
        print("{} mismatch(es).".format(len(errors)))
        return 1
    print("All checks passed (native graphics cmod vs src/lib/graphics).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130) from None
