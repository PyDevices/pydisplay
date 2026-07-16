# SPDX-License-Identifier: MIT
"""Driver assist / ADAS status."""

import lvgl as lv

import theme
from screens._common import content_size, make_bar, make_button, make_switch, prep_page, section_label


class AssistScreen:
    def __init__(self, page, vehicle, group, w=0, h=0):
        self.vehicle = vehicle
        w, h = content_size(prep_page(page, w, h), w, h)
        font = theme.pick_font(200, page)

        section_label(page, "DRIVER ASSIST", 4)
        self.switches = {}
        y = 36
        for key, label in (
            ("acc", "Adaptive cruise"),
            ("lane_keep", "Lane keep"),
            ("blind_spot", "Blind spot"),
        ):
            lbl = lv.label(page)
            lbl.set_text(label)
            lbl.set_style_text_color(theme.text(), 0)
            theme.apply_font(lbl, font)
            lbl.set_pos(8, y + 8)
            sw = make_switch(page, group)
            sw.set_pos(w - 72, y + 4)
            if vehicle.assist.get(key):
                sw.add_state(lv.STATE.CHECKED)

            def _make(k, switch):
                def _cb(e):
                    vehicle.assist[k] = bool(switch.has_state(lv.STATE.CHECKED))

                return _cb

            sw.add_event_cb(_make(key, sw), lv.EVENT.VALUE_CHANGED, None)
            self.switches[key] = sw
            y += 46

        self.acc_lbl = lv.label(page)
        self.acc_lbl.set_style_text_color(theme.accent_lite(), 0)
        theme.apply_font(self.acc_lbl, font)
        self.acc_lbl.set_pos(8, y + 4)

        minus = make_button(page, "− SET", 88, 36, group)
        plus = make_button(page, "+ SET", 88, 36, group)
        minus.set_pos(8, y + 32)
        plus.set_pos(104, y + 32)

        def _dec(e):
            vehicle.assist["acc_set"] = max(25, int(vehicle.assist["acc_set"]) - 5)

        def _inc(e):
            vehicle.assist["acc_set"] = min(85, int(vehicle.assist["acc_set"]) + 5)

        minus.add_event_cb(_dec, lv.EVENT.CLICKED, None)
        plus.add_event_cb(_inc, lv.EVENT.CLICKED, None)

        section_label(page, "PARKING SENSORS", y + 84)
        y += 112
        self.bars = {}
        for key, label in (
            ("park_fl", "FL"),
            ("park_fr", "FR"),
            ("park_rl", "RL"),
            ("park_rr", "RR"),
        ):
            lbl = lv.label(page)
            lbl.set_text(label)
            lbl.set_style_text_color(theme.text(), 0)
            theme.apply_font(lbl, font)
            lbl.set_pos(8, y + 2)
            bar = make_bar(page, w - 52, 16)
            bar.set_pos(44, y)
            self.bars[key] = bar
            y += 30

        self.update()

    def update(self):
        a = self.vehicle.assist
        on = "ON" if a.get("acc") else "OFF"
        self.acc_lbl.set_text("ACC set %d mph  [%s]" % (int(a.get("acc_set", 0)), on))
        for key, bar in self.bars.items():
            prox = float(a.get(key, 0.5))
            bar.set_value(int((1.0 - prox) * 100), 0)


def build(page, vehicle, group, w=0, h=0):
    return AssistScreen(page, vehicle, group, w, h)
