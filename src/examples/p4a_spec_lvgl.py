# gallery: skip
# SPDX-License-Identifier: MIT
"""
p4a_spec_lvgl
====================================================
CPython LVGL editor for an Android ``buildozer.spec``.

Desktop window defaults to landscape 1280x720 (override with
``PYDISPLAY_WIDTH`` / ``PYDISPLAY_HEIGHT``). Emitted ``orientation`` follows
the loaded template (portrait for the paint defaults).

Business logic: :mod:`p4a_spec_engine`. Generated file lands beside this
script as ``buildozer.spec`` — copy it to
``pydisplay_android/p4a_app/buildozer.spec``.
"""

from __future__ import annotations

import sys

_EXAMPLES = __file__.replace("\\", "/").rsplit("/", 1)[0]
if _EXAMPLES not in sys.path:
    sys.path.insert(0, _EXAMPLES)

from displaysys import env_get, env_set  # noqa: E402

if env_get("PYDISPLAY_WIDTH") is None:
    env_set("PYDISPLAY_WIDTH", "1280")
if env_get("PYDISPLAY_HEIGHT") is None:
    env_set("PYDISPLAY_HEIGHT", "720")
if env_get("PYDISPLAY_SCALE") is None:
    env_set("PYDISPLAY_SCALE", "1")

import display_driver  # noqa: E402 — wires LVGL display/input into the runtime
import lvgl as lv  # noqa: E402
from board_config import display_drv, runtime  # noqa: E402
from p4a_spec_engine import (  # noqa: E402
    ARCHS,
    BOOL_KEYS_01,
    BOOL_KEYS_TRUEFALSE,
    ORIENTATIONS,
    PERMISSIONS,
    SpecModel,
    load_defaults,
    write_output,
)

_styles = []
_model: SpecModel | None = None
_status = None
_fields = {}  # (section, key) -> widget/controller
_perm_checks = {}
_arch_checks = {}


def _hex(rgb):
    return lv.color_hex(rgb)


def _pick_font(unit, ref_obj=None):
    if unit >= 560:
        candidates = (22, 20, 18, 16, 14, 12)
    elif unit >= 400:
        candidates = (18, 16, 14, 12)
    else:
        candidates = (14, 12)
    for size in candidates:
        font = getattr(lv, "font_montserrat_" + str(size), None)
        if font is not None:
            return font
    if ref_obj is not None:
        for getter in ("theme_get_font_normal", "theme_get_font_small"):
            fn = getattr(lv, getter, None)
            if fn is None:
                continue
            try:
                font = fn(ref_obj)
                if font is not None:
                    return font
            except Exception:
                pass
    fn = getattr(lv, "font_get_default", None)
    if fn is not None:
        try:
            return fn()
        except Exception:
            pass
    return None


def _apply_font(obj, font):
    if font is not None:
        obj.set_style_text_font(font, 0)


def _style_bg(obj, color, radius=0):
    style = lv.style_t()
    style.init()
    style.set_bg_color(color)
    style.set_bg_opa(lv.OPA.COVER)
    style.set_radius(radius)
    style.set_border_width(0)
    style.set_pad_all(4)
    obj.add_style(style, 0)
    _styles.append(style)
    return style


def _set_status(msg):
    if _status is not None:
        _status.set_text(msg)


def _collect_into_model():
    assert _model is not None
    for (section, key), ctrl in _fields.items():
        kind = ctrl["kind"]
        if kind == "text":
            _model.set(key, ctrl["widget"].get_text(), section=section)
        elif kind == "dropdown":
            idx = ctrl["widget"].get_selected()
            opts = ctrl["options"]
            if 0 <= idx < len(opts):
                _model.set(key, opts[idx], section=section)
        elif kind == "switch":
            on = ctrl["widget"].has_state(lv.STATE.CHECKED)
            _model.bool_set(key, on, section=section)
        elif kind == "permissions":
            selected = [p for p, cb in _perm_checks.items() if cb.has_state(lv.STATE.CHECKED)]
            _model.list_set(key, selected, section=section)
        elif kind == "archs":
            selected = [a for a, cb in _arch_checks.items() if cb.has_state(lv.STATE.CHECKED)]
            _model.list_set(key, selected, section=section)


def _do_write(e=None):
    _collect_into_model()
    path = write_output(_model)
    _set_status("Wrote {} — copy to pydisplay_android/p4a_app/buildozer.spec".format(path))


def _add_label(parent, text, font, y, w):
    lbl = lv.label(parent)
    lbl.set_text(text)
    lbl.set_style_text_color(_hex(0xAEAEB2), 0)
    _apply_font(lbl, font)
    lbl.set_width(w)
    lbl.set_pos(8, y)
    return lbl


def _add_textarea(parent, value, font, y, w, h=36):
    ta = lv.textarea(parent)
    ta.set_one_line(True)
    ta.set_text("" if value is None else str(value))
    ta.set_size(w - 16, h)
    ta.set_pos(8, y)
    _apply_font(ta, font)
    return ta


def _add_switch(parent, on, y):
    sw = lv.switch(parent)
    sw.set_pos(8, y)
    if on:
        sw.add_state(lv.STATE.CHECKED)
    else:
        sw.remove_state(lv.STATE.CHECKED)
    return sw


def _add_dropdown(parent, options, current, font, y, w):
    dd = lv.dropdown(parent)
    dd.set_options("\n".join(options))
    try:
        idx = options.index(current)
    except ValueError:
        idx = 0
    dd.set_selected(idx)
    dd.set_width(w - 16)
    dd.set_pos(8, y)
    _apply_font(dd, font)
    return dd


def _add_check_column(parent, catalog, selected, font, y, w, height, store):
    cont = lv.obj(parent)
    cont.set_size(w - 16, height)
    cont.set_pos(8, y)
    _style_bg(cont, _hex(0x1C1C1E), 6)
    if hasattr(cont, "add_flag"):
        cont.add_flag(lv.obj.FLAG.SCROLLABLE)
    selected_set = set(selected)
    row = 4
    for name in catalog:
        cb = lv.checkbox(cont)
        cb.set_text(name)
        _apply_font(cb, font)
        cb.set_pos(4, row)
        if name in selected_set:
            cb.add_state(lv.STATE.CHECKED)
        store[name] = cb
        row += 28
    return cont


def build_ui():
    global _model, _status, _fields, _perm_checks, _arch_checks

    inst = display_driver.event_loop.current_instance()
    if inst is not None:
        inst.disable()
    try:
        _styles.clear()
        _fields = {}
        _perm_checks = {}
        _arch_checks = {}
        _model = load_defaults()

        W = display_drv.width
        H = display_drv.height
        unit = min(W, H)
        pad = max(6, unit // 64)
        header_h = max(56, H // 10)
        footer_h = max(48, H // 12)
        font = _pick_font(unit)
        font_sm = _pick_font(max(200, unit // 2))

        scr = lv.screen_active()
        _style_bg(scr, _hex(0x121214))

        header = lv.obj(scr)
        header.set_size(W, header_h)
        header.set_pos(0, 0)
        _style_bg(header, _hex(0x1C1C1E))
        if hasattr(header, "remove_flag"):
            header.remove_flag(lv.obj.FLAG.SCROLLABLE)

        title = lv.label(header)
        title.set_text("buildozer.spec editor")
        title.set_style_text_color(_hex(0xFFFFFF), 0)
        _apply_font(title, font)
        title.align(lv.ALIGN.TOP_LEFT, pad, pad // 2)

        _status = lv.label(header)
        src = _model.source_path or "(baked-in paint defaults)"
        _status.set_text("Defaults: {}".format(src))
        _status.set_style_text_color(_hex(0xAEAEB2), 0)
        _apply_font(_status, font_sm)
        _status.set_width(W - 2 * pad)
        _status.align(lv.ALIGN.BOTTOM_LEFT, pad, -pad // 2)
        if hasattr(_status, "set_long_mode"):
            _status.set_long_mode(lv.label.LONG_MODE.WRAP)

        footer = lv.obj(scr)
        footer.set_size(W, footer_h)
        footer.set_pos(0, H - footer_h)
        _style_bg(footer, _hex(0x1C1C1E))
        if hasattr(footer, "remove_flag"):
            footer.remove_flag(lv.obj.FLAG.SCROLLABLE)

        write_btn = lv.button(footer)
        write_btn.set_size(min(200, W // 3), footer_h - 2 * pad)
        write_btn.align(lv.ALIGN.RIGHT_MID, -pad, 0)
        _style_bg(write_btn, _hex(0x0A84FF), 8)
        wl = lv.label(write_btn)
        wl.set_text("Write")
        wl.set_style_text_color(_hex(0xFFFFFF), 0)
        _apply_font(wl, font_sm)
        wl.center()
        write_btn.add_event_cb(_do_write, lv.EVENT.CLICKED, None)

        hint = lv.label(footer)
        hint.set_text("Copy emitted buildozer.spec into pydisplay_android/p4a_app/")
        hint.set_style_text_color(_hex(0x8E8E93), 0)
        _apply_font(hint, font_sm)
        hint.set_width(W - min(200, W // 3) - 3 * pad)
        hint.align(lv.ALIGN.LEFT_MID, pad, 0)

        form = lv.obj(scr)
        form.set_size(W, H - header_h - footer_h)
        form.set_pos(0, header_h)
        _style_bg(form, _hex(0x121214))
        if hasattr(form, "add_flag"):
            form.add_flag(lv.obj.FLAG.SCROLLABLE)

        y = pad
        field_w = W - 2 * pad
        for section, key in _model.editable_keys():
            label = "{}: {}".format(section, key) if section != "app" else key
            _add_label(form, label, font_sm, y, field_w)
            y += 22

            if key == "orientation" and section == "app":
                cur = _model.get(key) or "portrait"
                dd = _add_dropdown(form, list(ORIENTATIONS), cur, font_sm, y, field_w)
                _fields[(section, key)] = {"kind": "dropdown", "widget": dd, "options": list(ORIENTATIONS)}
                y += 44
            elif key == "android.permissions" and section == "app":
                h = min(220, max(120, H // 3))
                _add_check_column(
                    form, PERMISSIONS, _model.list_get(key), font_sm, y, field_w, h, _perm_checks
                )
                _fields[(section, key)] = {"kind": "permissions"}
                y += h + 12
            elif key == "android.archs" and section == "app":
                h = min(140, max(100, H // 5))
                _add_check_column(
                    form, ARCHS, _model.list_get(key), font_sm, y, field_w, h, _arch_checks
                )
                _fields[(section, key)] = {"kind": "archs"}
                y += h + 12
            elif key in BOOL_KEYS_TRUEFALSE or key in BOOL_KEYS_01 or key in (
                "android.skip_update",
                "fullscreen",
            ):
                sw = _add_switch(form, _model.bool_get(key, section=section), y)
                _fields[(section, key)] = {"kind": "switch", "widget": sw}
                y += 44
            else:
                ta = _add_textarea(form, _model.get(key, section=section), font_sm, y, field_w)
                _fields[(section, key)] = {"kind": "text", "widget": ta}
                y += 44

        # Ensure form content height for scrolling.
        form.set_style_pad_bottom(pad, 0)
        spacer = lv.obj(form)
        spacer.set_size(field_w, 8)
        spacer.set_pos(8, y)

        # Mode C: emit on load.
        path = write_output(_model)
        _set_status(
            "Defaults: {} | Auto-wrote {}".format(_model.source_path or "(baked-in)", path)
        )
    finally:
        if inst is not None:
            inst.enable()


build_ui()
runtime.run_forever()
