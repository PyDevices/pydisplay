# SPDX-License-Identifier: MIT
"""Default center screen: large speedometer + odometer."""

import lvgl as lv

import gauges
import lv_util
import theme
from screens._common import content_size, make_button, prep_page


class SpeedScreen:
    def __init__(self, page, vehicle, group, w=0, h=0):
        self.vehicle = vehicle
        w, h = content_size(prep_page(page, w, h), w, h)

        pad = 8
        body_h = h - 72
        body_w = w - 2 * pad

        self.digital = gauges.make_digital_speed(page, body_w, int(body_h * 0.78))
        self.digital.set_pos(pad, 8)

        gauge_sz = min(body_w - 16, int(body_h * 0.78))
        self.analog = gauges.make_speed_gauge(page, gauge_sz)
        self.analog.set_pos((w - gauge_sz) // 2, 8)
        lv_util.hide(self.analog.widget())

        self.odo = lv.label(page)
        self.odo.set_style_text_color(theme.text(), 0)
        theme.apply_font(self.odo, theme.pick_font(220, page))
        self.odo.set_style_pad_all(0, 0)
        self.odo.align(lv.ALIGN.BOTTOM_LEFT, pad + 4, -10)

        self.gear = lv.label(page)
        self.gear.set_style_text_color(theme.accent_lite(), 0)
        theme.apply_font(self.gear, theme.pick_font(240, page))
        self.gear.set_style_pad_all(0, 0)
        self.gear.align(lv.ALIGN.BOTTOM_RIGHT, -pad - 4, -44)

        self.flags = lv.label(page)
        self.flags.set_style_text_color(theme.warn(), 0)
        theme.apply_font(self.flags, theme.pick_font(180, page))
        self.flags.set_style_pad_all(0, 0)
        self.flags.align(lv.ALIGN.BOTTOM_MID, 0, -10)

        self.toggle = make_button(page, "DIG / GAUGE", min(140, w // 3), 36, group)
        self.toggle.align(lv.ALIGN.BOTTOM_RIGHT, -pad, -6)

        def _toggle(e):
            vehicle.toggle_speedo_mode()
            self._apply_mode()

        self.toggle.add_event_cb(_toggle, lv.EVENT.CLICKED, None)
        lv_util.add_flag(self.digital.widget(), lv.obj.FLAG.CLICKABLE)
        self.digital.widget().add_event_cb(_toggle, lv.EVENT.CLICKED, None)
        self._apply_mode()
        self.update()

    def _apply_mode(self):
        digital = self.vehicle.speedo_mode == "digital"
        if digital:
            lv_util.show(self.digital.widget())
            lv_util.hide(self.analog.widget())
        else:
            lv_util.hide(self.digital.widget())
            lv_util.show(self.analog.widget())

    def update(self):
        v = self.vehicle
        mph = int(round(v.speed_mph))
        self._apply_mode()
        if v.speedo_mode == "digital":
            self.digital.set_value(mph)
        else:
            self.analog.set_value(min(125, mph))
        self.odo.set_text("ODO  %d mi" % int(v.odo_miles))
        self.gear.set_text("GEAR  %s" % v.gear_label())
        bits = []
        if v.lights.get("high_beam"):
            bits.append("HB")
        if v.lights.get("turn_left"):
            bits.append("<")
        if v.lights.get("turn_right"):
            bits.append(">")
        if v.redline:
            bits.append("REDLINE")
        self.flags.set_text("  ".join(bits) if bits else "")


def build(page, vehicle, group, w=0, h=0):
    return SpeedScreen(page, vehicle, group, w, h)
