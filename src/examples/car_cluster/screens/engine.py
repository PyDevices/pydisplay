# SPDX-License-Identifier: MIT
"""Engine information screen."""

import theme
from screens._common import content_size, kv_row, make_bar, prep_page, section_label, spread_rows


class EngineScreen:
    def __init__(self, page, vehicle, group, w=0, h=0):
        self.vehicle = vehicle
        w, h = content_size(prep_page(page, w, h), w, h)

        keys = (
            "Coolant",
            "Oil temp",
            "Oil pressure",
            "Battery",
            "Intake air",
            "Engine hours",
            "RPM",
        )
        ys = spread_rows(len(keys), top=8, bottom=56, height=h)
        self.vals = []
        for lab, y in zip(keys, ys):
            _k, v = kv_row(page, y, lab, "--", w)
            self.vals.append(v)

        load_y = h - 44
        section_label(page, "ENGINE LOAD", load_y - 22)
        self.load_bar = make_bar(page, w - 24, 18)
        self.load_bar.set_pos(8, load_y)
        self.update()

    def update(self):
        v = self.vehicle
        texts = (
            "%.1f °F" % v.coolant_f,
            "%.0f °F" % v.oil_temp_f,
            "%.1f psi" % v.oil_psi,
            "%.1f V" % v.battery_v,
            "%.0f °F" % v.iat_f,
            "%.1f h" % v.engine_hours,
            "%d" % int(v.rpm),
        )
        for lbl, text in zip(self.vals, texts):
            lbl.set_text(text)
        if v.coolant_f >= 212:
            self.vals[0].set_style_text_color(theme.danger(), 0)
        else:
            self.vals[0].set_style_text_color(theme.text(), 0)
        self.load_bar.set_value(int(v.throttle * 100), 0)


def build(page, vehicle, group, w=0, h=0):
    return EngineScreen(page, vehicle, group, w, h)
