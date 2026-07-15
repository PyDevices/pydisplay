# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Compare native ``graphics`` cmod to staged ``src/lib/graphics`` (``graphics_py``).

Loads both implementations in one interpreter: ``import graphics`` (native cmod)
and a copy of the pure-Python tree under ``.cursor/compare_graphics_py/graphics_py``.
Paired ``FrameBuffer`` draws are compared byte-for-byte.

Used by ``compare_graphics_run.py`` (single runtime) and
``compare_graphics_matrix.py`` (all desktop runtimes).
"""

import json
import sys

RESULT_PREFIX = "GRAPHICS_COMPARE_RESULT="

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

# Printable ASCII for per-glyph font probes (catches romfont index / mapping bugs).
_GLYPH_PROBE = "".join(chr(c) for c in range(32, 127))
_FONT_PROBE_STRING = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$"


def _dirname(path: str) -> str:
    path = path.replace("\\", "/")
    i = path.rfind("/")
    if i < 0:
        return "."
    if i == 0:
        return "/"
    return path[:i]


def _file_exists(path: str) -> bool:
    try:
        with open(path):
            pass
        return True
    except OSError:
        return False


def find_repo_root(start=None):
    p = start or _dirname(__file__).replace("\\", "/")
    for _ in range(8):
        if _file_exists(p + "/src/add_ons/framebuf.py"):
            return p
        p = _dirname(p)
    return None


def _makedirs(path: str) -> None:
    if not path or path == ".":
        return
    import os

    path = path.replace("\\", "/")
    parts = [part for part in path.split("/") if part]
    if not parts:
        return
    if path.startswith("/"):
        cur = "/" + parts[0]
        rest = parts[1:]
    else:
        cur = parts[0]
        rest = parts[1:]
    try:
        os.mkdir(cur)
    except OSError:
        pass
    for part in rest:
        cur = cur + "/" + part
        try:
            os.mkdir(cur)
        except OSError:
            pass


def _rgb565_buf(w: int, h: int) -> bytearray:
    return bytearray(w * h * 2 + 16)


def _paired_rgb565(native, py, w: int, h: int):
    nbuf = _rgb565_buf(w, h)
    pbuf = _rgb565_buf(w, h)
    fb_n = native.FrameBuffer(nbuf, w, h, native.RGB565)
    fb_p = py.FrameBuffer(pbuf, w, h, py.RGB565)
    return fb_n, fb_p, nbuf, pbuf


class _Reporter:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.errors = []
        self.skipped = []
        self.passed = 0

    def ok(self, label: str) -> None:
        self.passed += 1
        if self.verbose:
            print("ok:", label)

    def fail(self, msg: str) -> None:
        self.errors.append(msg)
        if self.verbose:
            print("FAIL:", msg)

    def skip(self, msg: str) -> None:
        self.skipped.append(msg)
        if self.verbose:
            print("skip:", msg)


def _compare_buffers(rep: _Reporter, label: str, nbuf, pbuf, length: int) -> None:
    nb = bytes(nbuf[:length])
    pb = bytes(pbuf[:length])
    if nb != pb:
        diff = sum(1 for a, b in zip(nb, pb) if a != b)
        rep.fail("{}: buffer mismatch ({} bytes differ)".format(label, diff))
        return
    rep.ok(label)


def _compare_value(rep: _Reporter, label: str, native_val, py_val) -> None:
    if native_val != py_val:
        rep.fail("{}: native={!r} python={!r}".format(label, native_val, py_val))
        return
    rep.ok(label)


def _framebuffer_has(native, py, name):
    return hasattr(native.FrameBuffer, name) and hasattr(py.FrameBuffer, name)


def _skip_unless_framebuffer(rep, native, py, name):
    if _framebuffer_has(native, py, name):
        return True
    rep.skip("FrameBuffer.{} not on native cmod".format(name))
    return False


def _draw_has(native, py, name):
    return hasattr(native.Draw, name) and hasattr(py.Draw, name)


def _skip_unless_draw(rep, native, py, name):
    if _draw_has(native, py, name):
        return True
    rep.skip("Draw.{} not on native cmod".format(name))
    return False


def stage_python_graphics(repo: str):
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


def _check_exports(rep: _Reporter, native, py) -> None:
    try:
        n_impl = native.implementation()
    except Exception as exc:
        rep.fail("native implementation(): {}".format(exc))
        n_impl = None
    else:
        if n_impl != "native_cmod":
            rep.fail("native implementation: {!r} (expected 'native_cmod')".format(n_impl))
        else:
            rep.ok("native implementation")

    try:
        p_impl = py.implementation()
    except Exception as exc:
        rep.fail("python implementation(): {}".format(exc))
        p_impl = None
    else:
        if p_impl != "pydisplay_python":
            rep.fail("python implementation: {!r} (expected 'pydisplay_python')".format(p_impl))
        else:
            rep.ok("python implementation")

    for name in _PYDISPLAY_ALL:
        if not hasattr(native, name):
            rep.fail("native missing export: " + name)
        elif not hasattr(py, name):
            rep.fail("python missing export: " + name)
        else:
            rep.ok("export " + name)


def _check_constants(rep: _Reporter, native, py) -> None:
    for name in _FORMAT_CONSTS:
        nv = getattr(native, name, None)
        pv = getattr(py, name, None)
        if nv != pv:
            rep.fail("constant {}: native={} python={}".format(name, nv, pv))
        else:
            rep.ok("constant " + name)


def _check_area(rep: _Reporter, native, py) -> None:
    a_n = native.Area(0, 0, 10, 10)
    a_p = py.Area(0, 0, 10, 10)
    _compare_value(rep, "Area contains", a_n.contains(5, 5), a_p.contains(5, 5))
    _compare_value(rep, "Area half-open edge", a_n.contains(10, 10), a_p.contains(10, 10))
    _compare_value(
        rep,
        "Area intersects",
        native.Area(0, 0, 5, 5).intersects(native.Area(4, 4, 5, 5)),
        py.Area(0, 0, 5, 5).intersects(py.Area(4, 4, 5, 5)),
    )
    _compare_value(
        rep,
        "Area union",
        native.Area(0, 0, 2, 2) + native.Area(4, 4, 2, 2),
        py.Area(0, 0, 2, 2) + py.Area(4, 4, 2, 2),
    )
    _compare_value(rep, "Area repr", repr(a_n), repr(a_p))


def _check_framebuffer_ops(rep: _Reporter, native, py) -> None:
    w, h = 16, 16
    length = w * h * 2

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0xF800)
    fb_p.fill(0xF800)
    _compare_buffers(rep, "FrameBuffer fill", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.pixel(3, 4, 0xBEEF)
    fb_p.pixel(3, 4, 0xBEEF)
    _compare_buffers(rep, "FrameBuffer pixel", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.fill_rect(2, 2, 5, 5, 0x07E0)
    fb_p.fill_rect(2, 2, 5, 5, 0x07E0)
    _compare_buffers(rep, "FrameBuffer fill_rect", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.hline(1, 3, 8, 0x1234)
    fb_p.hline(1, 3, 8, 0x1234)
    _compare_buffers(rep, "FrameBuffer hline", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.vline(3, 2, 10, 0x4321)
    fb_p.vline(3, 2, 10, 0x4321)
    _compare_buffers(rep, "FrameBuffer vline", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.line(0, 0, 10, 10, 0x00FF)
    fb_p.line(0, 0, 10, 10, 0x00FF)
    _compare_buffers(rep, "FrameBuffer line", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.rect(4, 4, 6, 6, 0xFFFF)
    fb_p.rect(4, 4, 6, 6, 0xFFFF)
    _compare_buffers(rep, "FrameBuffer rect", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.ellipse(8, 8, 4, 4, 0xF81F)
    fb_p.ellipse(8, 8, 4, 4, 0xF81F)
    _compare_buffers(rep, "FrameBuffer ellipse", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.circle(8, 8, 4, 0x8410)
    fb_p.circle(8, 8, 4, 0x8410)
    _compare_buffers(rep, "FrameBuffer circle", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.circle(8, 8, 4, 0x8410, True)
    fb_p.circle(8, 8, 4, 0x8410, True)
    _compare_buffers(rep, "FrameBuffer circle filled", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.round_rect(2, 2, 10, 8, 2, 0xABCD)
    fb_p.round_rect(2, 2, 10, 8, 2, 0xABCD)
    _compare_buffers(rep, "FrameBuffer round_rect", nbuf, pbuf, length)

    if _skip_unless_framebuffer(rep, native, py, "arc"):
        fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
        fb_n.fill(0)
        fb_p.fill(0)
        fb_n.arc(8, 8, 6, 0, 90, 0xF800)
        fb_p.arc(8, 8, 6, 0, 90, 0xF800)
        _compare_buffers(rep, "FrameBuffer arc", nbuf, pbuf, length)

    if _skip_unless_framebuffer(rep, native, py, "gradient_rect"):
        fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
        fb_n.fill(0)
        fb_p.fill(0)
        fb_n.gradient_rect(0, 0, 16, 16, 0xF800, 0x001F)
        fb_p.gradient_rect(0, 0, 16, 16, 0xF800, 0x001F)
        _compare_buffers(rep, "FrameBuffer gradient_rect", nbuf, pbuf, length)

    import array

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    pts = array.array("h", [2, 2, 12, 2, 12, 10, 2, 10])
    fb_n.poly(0, 0, pts, 0x8410)
    fb_p.poly(0, 0, pts, 0x8410)
    _compare_buffers(rep, "FrameBuffer poly", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0)
    fb_p.fill(0)
    fb_n.text("A", 1, 1, 1)
    fb_p.text("A", 1, 1, 1)
    _compare_buffers(rep, "FrameBuffer text", nbuf, pbuf, length)

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
    _compare_buffers(rep, "FrameBuffer blit", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    fb_n.fill(0x1234)
    fb_p.fill(0x1234)
    fb_n.pixel(0, 0, 0xABCD)
    fb_p.pixel(0, 0, 0xABCD)
    fb_n.scroll(2, 1)
    fb_p.scroll(2, 1)
    _compare_buffers(rep, "FrameBuffer scroll", nbuf, pbuf, length)


def _check_module_shapes(rep: _Reporter, native, py) -> None:
    w, h = 32, 32
    length = w * h * 2

    def run(label, draw):
        fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
        draw(native, py, fb_n, fb_p)
        _compare_buffers(rep, label, nbuf, pbuf, length)

    run(
        "fill()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.fill(fn, 0x1234),
            p.fill(fp, 0x1234),
        ),
    )
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
        "round_rect()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.round_rect(fn, 4, 4, 12, 10, 3, 0xABCD),
            p.round_rect(fp, 4, 4, 12, 10, 3, 0xABCD),
        ),
    )
    run(
        "arc()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.arc(fn, 16, 16, 10, 0, 120, 0xF800),
            p.arc(fp, 16, 16, 10, 0, 120, 0xF800),
        ),
    )
    run(
        "gradient_rect()",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.gradient_rect(fn, 0, 0, 32, 32, 0xF800, 0x001F),
            p.gradient_rect(fp, 0, 0, 32, 32, 0xF800, 0x001F),
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


def _check_draw(rep: _Reporter, native, py) -> None:
    w, h = 32, 32
    length = w * h * 2

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    native.Draw(fb_n).fill_rect(1, 1, 6, 6, 0x1234)
    py.Draw(fb_p).fill_rect(1, 1, 6, 6, 0x1234)
    _compare_buffers(rep, "Draw.fill_rect", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    native.Draw(fb_n).line(0, 0, 15, 15, 0x07E0)
    py.Draw(fb_p).line(0, 0, 15, 15, 0x07E0)
    _compare_buffers(rep, "Draw.line", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    native.Draw(fb_n).circle(16, 16, 8, 0x8410)
    py.Draw(fb_p).circle(16, 16, 8, 0x8410)
    _compare_buffers(rep, "Draw.circle", nbuf, pbuf, length)

    fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
    native.Draw(fb_n).round_rect(2, 2, 12, 10, 2, 0xABCD)
    py.Draw(fb_p).round_rect(2, 2, 12, 10, 2, 0xABCD)
    _compare_buffers(rep, "Draw.round_rect", nbuf, pbuf, length)

    if _skip_unless_draw(rep, native, py, "text8"):
        fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
        native.Draw(fb_n).text8("Z", 0, 0, 0xFFFF)
        py.Draw(fb_p).text8("Z", 0, 0, 0xFFFF)
        _compare_buffers(rep, "Draw.text8", nbuf, pbuf, length)

    if _skip_unless_draw(rep, native, py, "clip"):
        fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
        fb_n.fill(0)
        fb_p.fill(0)
        with native.Draw(fb_n).clip(4, 4, 20, 20):
            native.Draw(fb_n).fill_rect(0, 0, 32, 32, 0xF800)
        with py.Draw(fb_p).clip(4, 4, 20, 20):
            py.Draw(fb_p).fill_rect(0, 0, 32, 32, 0xF800)
        _compare_buffers(rep, "Draw.clip fill_rect", nbuf, pbuf, length)


def _check_fonts(rep: _Reporter, native, py) -> None:
    w, h = 48, 48
    length = w * h * 2

    def run(label, draw):
        fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, w, h)
        draw(native, py, fb_n, fb_p)
        _compare_buffers(rep, label, nbuf, pbuf, length)

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
    run(
        "text8 probe string",
        lambda n, p, fn, fp: (
            fn.fill(0),
            fp.fill(0),
            n.text8(fn, _FONT_PROBE_STRING, 0, 0, 0xFFFF),
            p.text8(fp, _FONT_PROBE_STRING, 0, 0, 0xFFFF),
        ),
    )


def _check_font_glyph_grid(rep: _Reporter, native, py) -> None:
    """Per-codepoint probes — surfaces romfont index / glyph mapping bugs in cmod."""
    helpers = (
        ("text8", 8),
        ("text14", 14),
        ("text16", 16),
    )
    for helper_name, row_h in helpers:
        helper_n = getattr(native, helper_name)
        helper_p = getattr(py, helper_name)
        cell_w = 10
        for ch in _GLYPH_PROBE:
            label = "glyph {} U+{:04X} {!r}".format(helper_name, ord(ch), ch)
            fb_n, fb_p, nbuf, pbuf = _paired_rgb565(native, py, cell_w, row_h + 2)
            fb_n.fill(0)
            fb_p.fill(0)
            helper_n(fb_n, ch, 0, 0, 0xFFFF)
            helper_p(fb_p, ch, 0, 0, 0xFFFF)
            _compare_buffers(rep, label, nbuf, pbuf, len(nbuf))


def run_compare(repo, *, verbose=True):
    """Load native + staged python graphics and return a result dict."""
    rep = _Reporter(verbose=verbose)
    result = {
        "status": "error",
        "repo": repo,
        "native_impl": None,
        "python_impl": None,
        "checks_passed": 0,
        "errors": [],
        "skipped": [],
    }

    try:
        import graphics as native
    except ImportError as exc:
        result["error"] = "import graphics failed: {}".format(exc)
        return result

    try:
        py = stage_python_graphics(repo)
    except OSError as exc:
        result["error"] = "stage python graphics failed: {}".format(exc)
        return result

    try:
        result["native_impl"] = native.implementation()
    except Exception:
        result["native_impl"] = None
    try:
        result["python_impl"] = py.implementation()
    except Exception:
        result["python_impl"] = None

    _check_exports(rep, native, py)
    _check_constants(rep, native, py)
    _check_area(rep, native, py)
    _check_framebuffer_ops(rep, native, py)
    _check_module_shapes(rep, native, py)
    _check_draw(rep, native, py)
    _check_fonts(rep, native, py)
    _check_font_glyph_grid(rep, native, py)

    result["checks_passed"] = rep.passed
    result["errors"] = rep.errors
    result["skipped"] = rep.skipped
    if rep.errors:
        result["status"] = "error"
        result["error"] = rep.errors[0]
    else:
        result["status"] = "ok"
        result.pop("error", None)
    return result


def _parse_args(argv):
    repo = None
    verbose = True
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--repo", "-r") and i + 1 < len(argv):
            repo = argv[i + 1]
            i += 2
            continue
        if arg == "--quiet":
            verbose = False
            i += 1
            continue
        if arg in ("-h", "--help"):
            return {"help": True}
        i += 1
    if repo is None:
        repo = find_repo_root()
    return {"repo": repo, "verbose": verbose}


def main(argv=None):
    opts = _parse_args(argv if argv is not None else sys.argv[1:])
    if opts.get("help"):
        print(
            "Usage: compare_graphics_run.py [--repo PATH] [--quiet]\n"
            "Compare native graphics cmod vs staged src/lib/graphics."
        )
        return 0

    repo = opts.get("repo")
    if not repo:
        print("missing repo root (use --repo or run from pydisplay checkout)", file=sys.stderr)
        return 1

    result = run_compare(repo, verbose=opts.get("verbose", True))
    print(RESULT_PREFIX + json.dumps(result, separators=(",", ":")))

    if opts.get("verbose", True):
        print()
        if result["status"] == "ok":
            print(
                "All checks passed ({} ok, native graphics cmod vs src/lib/graphics).".format(
                    result["checks_passed"]
                )
            )
        elif result.get("error") and not result.get("errors"):
            print("Fatal:", result["error"])
        else:
            print("{} mismatch(es).".format(len(result.get("errors", []))))

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130) from None
