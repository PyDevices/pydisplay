# SPDX-License-Identifier: MIT
"""Nested 3D chrome bezels and focus styles for the cluster shell."""

import lvgl as lv

import theme


def _circle_radius():
    return getattr(lv, "RADIUS_CIRCLE", 0x7FFF)


def _no_scroll(obj):
    if hasattr(obj, "remove_flag"):
        obj.remove_flag(lv.obj.FLAG.SCROLLABLE)
    elif hasattr(obj, "clear_flag"):
        obj.clear_flag(lv.obj.FLAG.SCROLLABLE)


def style_root(obj):
    theme.style_bg(obj, theme.bg(), radius=0)


def style_panel(obj, radius=8):
    theme.style_bg(obj, theme.panel(), radius=radius, border_w=1, border_color=theme.chrome_mid())


def make_focus_style():
    """Accent ring for STATE.FOCUSED (rail / menu controls)."""
    style = lv.style_t()
    style.init()
    style.set_outline_width(2)
    style.set_outline_pad(2)
    style.set_outline_color(theme.accent())
    style.set_outline_opa(lv.OPA.COVER)
    style.set_border_width(2)
    style.set_border_color(theme.accent_lite())
    style.set_border_opa(lv.OPA.COVER)
    return theme.retain_style(style)


def make_bezel(parent, x, y, w, h, depth=3, radius=10, pad=3):
    """Stacked frames for a plastic/chrome edge. Returns (outer, content)."""
    outer = lv.obj(parent)
    outer.set_pos(x, y)
    outer.set_size(w, h)
    _no_scroll(outer)
    theme.style_bg(outer, theme.chrome_hi(), radius=radius, border_w=1, border_color=theme.chrome_mid())

    cur = outer
    inner_r = radius
    for i in range(depth):
        child = lv.obj(cur)
        _no_scroll(child)
        cur.set_style_pad_all(pad if i == 0 else max(1, pad - 1), 0)
        child.set_size(lv.pct(100), lv.pct(100))
        child.align(lv.ALIGN.CENTER, 0, 0)
        inner_r = max(2, inner_r - 2)
        if i == 0:
            theme.style_bg(child, theme.chrome_mid(), radius=inner_r)
        elif i == depth - 1:
            theme.style_bg(
                child, theme.face(), radius=inner_r, border_w=1, border_color=theme.chrome_lo()
            )
        else:
            theme.style_bg(
                child, theme.chrome_lo(), radius=inner_r, border_w=1, border_color=theme.chrome_hi()
            )
        cur = child

    content = cur
    # No content padding — callers position with set_pos against the full inner area.
    content.set_style_pad_all(0, 0)
    return outer, content


def make_center_bezel(parent, x, y, w, h):
    """Thicker, shinier bezel for the center instrument column."""
    return make_bezel(parent, x, y, w, h, depth=4, radius=14, pad=4)


def make_gauge_ring(parent, size):
    """Circular chrome ring + dark face for a gauge. Returns (ring, face)."""
    rad = _circle_radius()
    ring = lv.obj(parent)
    ring.set_size(size, size)
    _no_scroll(ring)
    theme.style_bg(ring, theme.chrome_hi(), radius=rad, border_w=2, border_color=theme.chrome_mid())
    face = lv.obj(ring)
    inset = max(4, size // 28)
    face.set_size(size - 2 * inset, size - 2 * inset)
    face.center()
    _no_scroll(face)
    theme.style_bg(face, theme.face(), radius=rad, border_w=1, border_color=theme.chrome_lo())
    return ring, face


def style_rail_button(btn, selected=False):
    theme.style_bg(
        btn,
        theme.panel_raised() if not selected else theme.accent_dim(),
        radius=8,
        border_w=1,
        border_color=theme.accent() if selected else theme.chrome_mid(),
    )
    btn.set_style_pad_all(2, 0)
    btn.set_style_pad_row(2, 0)
    focus = make_focus_style()
    btn.add_style(focus, lv.STATE.FOCUSED)
