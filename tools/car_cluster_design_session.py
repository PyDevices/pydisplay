#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Interactive design session for car_cluster (CPython desktop).

Freezes gauge/vehicle animation, keeps the SDL window live, and executes
snippets dropped into a command file so an agent or human can tweak layout
without restarting.

Usage (from repo root)::

    CAR_CLUSTER_FREEZE=1 PYDISPLAY_WIDTH=1200 PYDISPLAY_HEIGHT=560 \\
      .venv/bin/python tools/car_cluster_design_session.py

Then write Python into ``/tmp/car_cluster_design_cmd.py``. Namespace includes
``ui``, ``vehicle``, ``lv``, ``theme``, ``gauges``, ``apply_design_baseline``,
``apply_speed_layout``, ``apply_lights_layout``.
"""

from __future__ import annotations

import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
PKG = os.path.join(SRC, "examples", "car_cluster")
os.chdir(SRC)
for p in (SRC, PKG, os.path.join(SRC, "lib"), os.path.join(SRC, "add_ons")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("CAR_CLUSTER_FREEZE", "1")
os.environ.setdefault("PYDISPLAY_WIDTH", "1200")
os.environ.setdefault("PYDISPLAY_HEIGHT", "560")
os.environ.setdefault("PYDISPLAY_SCALE", "1")

CMD_PATH = os.environ.get("CAR_CLUSTER_DESIGN_CMD", "/tmp/car_cluster_design_cmd.py")
LOG_PATH = os.environ.get("CAR_CLUSTER_DESIGN_LOG", "/tmp/car_cluster_design_out.log")

import input_map  # noqa: E402

import lib.path  # noqa: E402, F401

input_map.capture_virtual_devices()

from displaysys import env_set  # noqa: E402

env_set("CAR_CLUSTER_FREEZE", "1")

from board_config import runtime  # noqa: E402
import car_cluster as cc  # noqa: E402
import display_driver  # noqa: E402
import lvgl as lv  # noqa: E402
import theme  # noqa: E402

from multimer import sleep_ms  # noqa: E402

cc.freeze(True)
ui = cc._ui
vehicle = cc._vehicle


def _log(*args, **kwargs) -> None:
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    line = sep.join(str(a) for a in args) + end
    sys.stdout.write(line)
    sys.stdout.flush()
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line)
    except Exception:
        pass


def _gauge_labels(g):
    """Return Python-held label refs only — never walk face children (segfaults)."""
    out = []
    for attr in ("title_lbl", "value_lbl", "cap_min_lbl", "cap_max_lbl"):
        lbl = getattr(g, attr, None)
        if lbl is not None:
            out.append(lbl)
    return out


def _set_scale(lbl, scale=512):
    w = max(1, lbl.get_width())
    h = max(1, lbl.get_height())
    lbl.set_style_transform_pivot_x(w // 2, 0)
    lbl.set_style_transform_pivot_y(h // 2, 0)
    try:
        lbl.set_style_transform_scale(scale, 0)
    except Exception:
        lbl.set_style_transform_scale_x(scale, 0)
        lbl.set_style_transform_scale_y(scale, 0)


def _set_scale_2x(lbl):
    _set_scale(lbl, 512)


def _set_scale_2x_edge(lbl, *, left=True):
    """2x scale pivoting on left or right edge so short labels stay flush."""
    w = max(1, lbl.get_width())
    h = max(1, lbl.get_height())
    lbl.set_style_transform_pivot_x(0 if left else w, 0)
    lbl.set_style_transform_pivot_y(h // 2, 0)
    try:
        lbl.set_style_transform_scale(512, 0)
    except Exception:
        lbl.set_style_transform_scale_x(512, 0)
        lbl.set_style_transform_scale_y(512, 0)


def _cap_mid(g, *, x_extra=0, y=0, bottom=False):
    """Mid-align min/max caps; optional extra inset and vertical offset."""
    if g is None:
        return
    x_ofs = max(8, g.size // 10) + x_extra
    align_l = lv.ALIGN.BOTTOM_LEFT if bottom else lv.ALIGN.LEFT_MID
    align_r = lv.ALIGN.BOTTOM_RIGHT if bottom else lv.ALIGN.RIGHT_MID
    y_ofs = -g.size // 6 if bottom else y
    for cap, align, x in (
        (getattr(g, "cap_min_lbl", None), align_l, x_ofs),
        (getattr(g, "cap_max_lbl", None), align_r, -x_ofs),
    ):
        if cap is None:
            continue
        cap.set_style_translate_x(0, 0)
        cap.set_style_translate_y(0, 0)
        try:
            cap.set_style_transform_scale(256, 0)
        except Exception:
            cap.set_style_transform_scale_x(256, 0)
            cap.set_style_transform_scale_y(256, 0)
        cap.align(align, x, y_ofs)
        _set_scale_2x(cap)


def apply_lights_layout():
    """Even spacing on Lights (EXTERIOR + Active fixed; slider near Active)."""
    if ui is None:
        return
    lights = ui.tabview.get_content().get_child(4)
    lpw = lights.get_width()
    ext = lights.get_child(0)
    ext.set_style_translate_x((lpw - max(1, ext.get_width())) // 2 - 4, 0)
    ext.set_style_translate_y(0, 0)
    virgin = {
        1: (8, 44),
        2: (232, 40),
        3: (8, 88),
        4: (232, 84),
        5: (8, 132),
        6: (232, 128),
        7: (8, 176),
        8: (232, 172),
        9: (8, 220),
        10: (232, 216),
        11: (4, 260),
        12: (8, 296),
        13: (232, 292),
        14: (4, 336),
        15: (8, 364),
    }
    n = 9
    y0, y_last = 32, 436
    step = (y_last - y0) / (n - 1)
    anchors = [round(y0 + i * step) for i in range(n)]

    def _place(i, tx, ty):
        obj = lights.get_child(i)
        vx, vy = virgin[i]
        obj.set_style_translate_x(tx - vx, 0)
        obj.set_style_translate_y(ty - vy, 0)

    for base, li, si in (
        (anchors[0], 1, 2),
        (anchors[1], 3, 4),
        (anchors[2], 5, 6),
        (anchors[3], 7, 8),
        (anchors[4], 9, 10),
    ):
        _place(li, 8, base + 8)
        _place(si, 232, base + 4)
    cab = lights.get_child(11)
    _place(11, (lpw - max(1, cab.get_width())) // 2, anchors[5])
    _place(12, 8, anchors[6] + 8)
    _place(13, 232, anchors[6] + 4)
    br = lights.get_child(14)
    _place(14, (lpw - max(1, br.get_width())) // 2, anchors[7])
    _place(15, 8, anchors[8])
    _log("LIGHTS_LAYOUT applied")


def apply_speed_layout():
    """Digital speed 8x / MPH 3x, DIG/GAUGE, odo, gear — Speed tab only."""
    if ui is None or not ui.screens:
        return
    try:
        ui.tabview.set_active(0, False)
    except TypeError:
        ui.tabview.set_active(0)
    vehicle.speedo_mode = "digital"
    page = ui.tabview.get_content().get_child(0)
    dig = page.get_child(0)
    ana = page.get_child(1)
    try:
        dig.remove_flag(lv.obj.FLAG.HIDDEN)
    except Exception:
        dig.clear_flag(lv.obj.FLAG.HIDDEN)
    ana.add_flag(lv.obj.FLAG.HIDDEN)

    unit = dig.get_child(2)
    scr = ui.screens[0]
    digital = getattr(scr, "digital", None)
    if digital is not None:
        digital.set_num_scale(2048)
        digital.num.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        unit = digital.unit
    else:
        shadow, num = dig.get_child(0), dig.get_child(1)
        bw, bh = dig.get_width(), dig.get_height()
        y_ofs = -bh // 12

        def _center_scaled(lbl, scale, x_ofs=0, y_ofs=0):
            lbl.set_width(bw)
            lbl.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
            lbl.set_style_translate_x(0, 0)
            lbl.set_style_translate_y(0, 0)
            lbl.align(lv.ALIGN.CENTER, x_ofs, y_ofs)
            w = max(1, lbl.get_width())
            h = max(1, lbl.get_height())
            lbl.set_style_transform_pivot_x(w // 2, 0)
            lbl.set_style_transform_pivot_y(h // 2, 0)
            try:
                lbl.set_style_transform_scale_x(scale, 0)
                lbl.set_style_transform_scale_y(scale, 0)
            except Exception:
                lbl.set_style_transform_scale(scale, 0)
            cx = lbl.get_x() + w // 2
            cy = lbl.get_y() + h // 2
            lbl.set_style_translate_x(bw // 2 + x_ofs - cx, 0)
            lbl.set_style_translate_y(bh // 2 + y_ofs - cy, 0)

        _center_scaled(num, 2048, 0, y_ofs)
        _center_scaled(shadow, 2048, 4, y_ofs + 4)
        num.set_style_text_color(lv.color_hex(0xFFFFFF), 0)

    uh = max(1, unit.get_height())
    unit.set_style_translate_x(0, 0)
    unit.set_style_translate_y(0, 0)
    unit.align(lv.ALIGN.BOTTOM_MID, 0, -12 - uh)
    _set_scale(unit, 768)
    odo = getattr(scr, "odo", None)
    toggle = getattr(scr, "toggle", None)
    gear = getattr(scr, "gear", None)

    if odo is not None:
        try:
            odo.set_text("%.1f mi" % float(vehicle.odo_miles))
        except Exception:
            pass
        odo.set_style_translate_x(0, 0)
        odo.set_style_translate_y(0, 0)
        odo.align(lv.ALIGN.BOTTOM_MID, 0, -10)
        _set_scale_2x(odo)
        # Keep bottom-center; do not reintroduce horizontal translate after scale.
        odo.set_style_translate_x(0, 0)

    if toggle is not None:
        toggle.set_style_translate_x(0, 0)
        toggle.set_style_translate_y(0, 0)
        toggle.align_to(dig, lv.ALIGN.OUT_BOTTOM_MID, 0, max(1, toggle.get_height()) // 2)

    if gear is not None and toggle is not None and odo is not None:
        # Same parent as odo; TOP_LEFT placement (BOTTOM_* + translate drifts off-page).
        if gear.get_parent() is not odo.get_parent():
            try:
                gear.set_parent(odo.get_parent())
            except Exception:
                pass
        gear.set_style_translate_x(0, 0)
        gear.set_style_translate_y(0, 0)
        try:
            lv.obj.update_layout(page)
        except Exception:
            pass
        gw = max(1, gear.get_width())
        gh = max(1, gear.get_height())
        btn_bot = toggle.get_y() + toggle.get_height()
        gap_mid = (btn_bot + odo.get_y()) // 2
        ty = gap_mid - gh // 2 + int(1.5 * gh) + 8 - 24
        ty = max(btn_bot + 2, min(ty, odo.get_y() - gh - 2))
        tx = (page.get_width() - gw) // 2
        gear.align(lv.ALIGN.TOP_LEFT, tx, ty)
        try:
            lv.obj.update_layout(page)
        except Exception:
            pass
        try:
            gear.move_foreground()
        except Exception:
            pass
        _set_scale_2x(gear)

    _log("SPEED_LAYOUT applied")


def apply_design_baseline():
    """Re-apply layout decisions from the interactive design session."""
    if ui is None:
        return

    for _name, g in ui.gauges.items():
        for lbl in _gauge_labels(g):
            _set_scale_2x(lbl)

    # RPM + analog SPEED: titles CENTER +48; RPM caps bottom inset.
    speed = getattr(ui.screens[0], "analog", None) if ui.screens else None
    for g in (ui.gauges.get("rpm"), speed):
        if g is None or getattr(g, "title_lbl", None) is None:
            continue
        for lbl in _gauge_labels(g):
            _set_scale_2x(lbl)
        lbl = g.title_lbl
        h = max(1, lbl.get_height())
        lbl.set_style_translate_x(0, 0)
        lbl.set_style_translate_y(0, 0)
        lbl.align(lv.ALIGN.CENTER, 0, 2 * (h + h // 2))
        _set_scale_2x(lbl)

    rpm = ui.gauges.get("rpm")
    if rpm is not None:
        cap0 = getattr(rpm, "cap_min_lbl", None)
        cap10 = getattr(rpm, "cap_max_lbl", None)
        w0 = max(1, cap0.get_width()) if cap0 is not None else 0
        w10 = max(1, cap10.get_width()) if cap10 is not None else 0
        _cap_mid(rpm, x_extra=2 * w10 + w0, bottom=True)

    if speed is not None and getattr(speed, "title_lbl", None) is not None:
        th = max(1, speed.title_lbl.get_height())
        ty = 2 * (th + th // 2)
        cap0 = getattr(speed, "cap_min_lbl", None)
        w0 = max(1, cap0.get_width()) if cap0 is not None else 0
        _cap_mid(speed, x_extra=w0, y=ty)

    temp = ui.gauges.get("temp")
    if temp is not None:
        title = getattr(temp, "title_lbl", None)
        if title is not None:
            h = max(1, title.get_height())
            title.set_style_translate_x(0, 0)
            title.set_style_translate_y(0, 0)
            title.align(lv.ALIGN.CENTER, 0, (h + h // 2) + (h + h // 2) // 2)
            _set_scale_2x(title)
        _cap_mid(temp)

    oil = ui.gauges.get("oil")
    if oil is not None:
        title = getattr(oil, "title_lbl", None)
        if title is not None:
            h = max(1, title.get_height())
            title.set_style_translate_x(0, 0)
            title.set_style_translate_y(0, 0)
            title.align(lv.ALIGN.CENTER, 0, h + h // 2)
            _set_scale_2x(title)
        cap0 = getattr(oil, "cap_min_lbl", None)
        w0 = max(1, cap0.get_width()) if cap0 is not None else 0
        _cap_mid(oil, x_extra=w0)

    fuel = ui.gauges.get("fuel")
    if fuel is not None:
        title = getattr(fuel, "title_lbl", None)
        if title is not None:
            h = max(1, title.get_height())
            title.set_style_translate_x(0, 0)
            title.set_style_translate_y(0, 0)
            title.align(lv.ALIGN.CENTER, 0, h + h // 2)
            _set_scale_2x(title)
        _cap_mid(fuel)
        value = getattr(fuel, "value_lbl", None)
        if value is not None:
            try:
                value.add_flag(lv.obj.FLAG.HIDDEN)
            except Exception:
                pass

    # Oil / coolant / analog speed value labels nudged up half height.
    value_up = [ui.gauges.get("oil"), ui.gauges.get("temp")]
    if ui.screens:
        value_up.append(getattr(ui.screens[0], "analog", None))
    for gauge in value_up:
        if gauge is None:
            continue
        value = getattr(gauge, "value_lbl", None)
        if value is None:
            continue
        h = max(1, value.get_height())
        y = -max(4, gauge.size // 14) - h // 2
        value.set_style_translate_x(0, 0)
        value.set_style_translate_y(0, 0)
        value.align(lv.ALIGN.BOTTOM_MID, 0, y)
        _set_scale_2x(value)

    # Trip A / Trip B + Engine (translate-only edge scale).
    try:
        content = ui.tabview.get_content()
        pad = 14
        for page_i in (1, 2):
            page = content.get_child(page_i)
            pw = page.get_width()
            label_h = max(1, page.get_child(0).get_height())
            try:
                _set_scale_2x(page.get_child(10).get_child(0))
            except Exception:
                pass
            for i in (0, 2, 4, 6, 8):
                lbl = page.get_child(i)
                _set_scale_2x_edge(lbl, left=True)
                lbl.set_style_translate_x(pad - 8, 0)
                lbl.set_style_translate_y(label_h, 0)
            for i in (1, 3, 5, 7, 9):
                lbl = page.get_child(i)
                w = max(1, lbl.get_width())
                _set_scale_2x_edge(lbl, left=False)
                lbl.set_style_translate_x(pw - pad - w - 152, 0)
                lbl.set_style_translate_y(label_h, 0)

        engine = content.get_child(3)
        pw = engine.get_width()
        label_h = max(1, engine.get_child(0).get_height())
        try:
            engine.get_child(4).set_text("Oil pres.")
            engine.get_child(10).set_text("Hours")
        except Exception:
            pass
        engine_ys = [8, 68, 128, 188, 248, 308, 368]
        engine_dy = label_h + 16
        for row, y0 in enumerate(engine_ys):
            y = y0 + engine_dy
            key = engine.get_child(row * 2)
            val = engine.get_child(row * 2 + 1)
            _set_scale_2x_edge(key, left=True)
            key.set_style_translate_x(pad - 8, 0)
            key.set_style_translate_y(y - y0, 0)
            w = max(1, val.get_width())
            _set_scale_2x_edge(val, left=False)
            val.set_style_translate_x(pw - pad - w - 152, 0)
            val.set_style_translate_y(y - y0, 0)
        try:
            engine.get_child(14).add_flag(lv.obj.FLAG.HIDDEN)
        except Exception:
            pass
    except Exception:
        _log(traceback.format_exc())

    try:
        apply_speed_layout()
    except Exception:
        _log(traceback.format_exc())

    try:
        apply_lights_layout()
    except Exception:
        _log(traceback.format_exc())

    _log("DESIGN_BASELINE applied")


def _ns():
    return {
        "ui": ui,
        "vehicle": vehicle,
        "lv": lv,
        "theme": theme,
        "gauges": ui.gauges if ui is not None else {},
        "cc": cc,
        "freeze": cc.freeze,
        "apply_design_baseline": apply_design_baseline,
        "apply_speed_layout": apply_speed_layout,
        "apply_lights_layout": apply_lights_layout,
        "print": _log,
    }


def _lvgl_idle() -> bool:
    try:
        return lv._nesting.value == 0
    except Exception:
        return True


def _run_cmd_file() -> None:
    if not _lvgl_idle():
        return
    if not os.path.isfile(CMD_PATH):
        return
    try:
        with open(CMD_PATH) as f:
            code = f.read()
        os.remove(CMD_PATH)
    except Exception as exc:
        _log("cmd-read-error: %r" % (exc,))
        return
    if not code.strip():
        return
    _log("--- exec ---")
    try:
        ns = _ns()
        exec(compile(code, CMD_PATH, "exec"), ns, ns)
        _log("OK")
    except Exception:
        _log(traceback.format_exc())


try:
    with open(LOG_PATH, "w") as f:
        f.write("")
except Exception:
    pass

apply_design_baseline()
_log(
    "DESIGN_SESSION ready freeze=%s gauges=%s cmd=%s"
    % (cc._FREEZE, list(ui.gauges.keys()) if ui else None, CMD_PATH)
)
_log("READY")

try:
    while not getattr(runtime, "quit_requested", False):
        _run_cmd_file()
        sleep_ms(50)
finally:
    try:
        runtime.request_quit()
    except Exception:
        pass
