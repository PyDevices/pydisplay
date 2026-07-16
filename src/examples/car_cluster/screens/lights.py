# SPDX-License-Identifier: MIT
"""Exterior / cabin light controls."""

import lvgl as lv

import theme
from screens._common import content_size, make_slider, make_switch, prep_page, section_label


class LightsScreen:
    def __init__(self, page, vehicle, group, w=0, h=0):
        self.vehicle = vehicle
        w, h = content_size(prep_page(page, w, h), w, h)
        font = theme.pick_font(200, page)

        section_label(page, "EXTERIOR", 4)
        self.switches = {}
        ext_rows = (
            ("autodim", "Auto dim"),
            ("delayed_off", "Delayed off"),
            ("drl", "Daytime running"),
            ("fog", "Fog lamps"),
            ("high_beam", "High beam"),
        )
        y = 36
        for key, label in ext_rows:
            lbl = lv.label(page)
            lbl.set_text(label)
            lbl.set_style_text_color(theme.text(), 0)
            theme.apply_font(lbl, font)
            lbl.set_pos(8, y + 8)
            sw = make_switch(page, group)
            sw.set_pos(w - 72, y + 4)
            if vehicle.lights.get(key):
                sw.add_state(lv.STATE.CHECKED)
            else:
                sw.remove_state(lv.STATE.CHECKED)

            def _make(k, switch):
                def _cb(e):
                    on = switch.has_state(lv.STATE.CHECKED)
                    vehicle.lights[k] = bool(on)
                    if k == "autodim" and on:
                        theme.set_brightness(0.75)
                    elif k == "cabin" and on:
                        theme.set_brightness(1.0)

                return _cb

            sw.add_event_cb(_make(key, sw), lv.EVENT.VALUE_CHANGED, None)
            self.switches[key] = sw
            y += 44

        section_label(page, "CABIN", y + 4)
        y += 32
        lbl = lv.label(page)
        lbl.set_text("Cabin lights")
        lbl.set_style_text_color(theme.text(), 0)
        theme.apply_font(lbl, font)
        lbl.set_pos(8, y + 8)
        sw = make_switch(page, group)
        sw.set_pos(w - 72, y + 4)
        if vehicle.lights.get("cabin"):
            sw.add_state(lv.STATE.CHECKED)

        def _cabin_cb(e, s=sw):
            vehicle.lights["cabin"] = bool(s.has_state(lv.STATE.CHECKED))
            if vehicle.lights["cabin"]:
                theme.set_brightness(1.0)

        sw.add_event_cb(_cabin_cb, lv.EVENT.VALUE_CHANGED, None)
        self.switches["cabin"] = sw
        y += 48

        section_label(page, "BRIGHTNESS", y)
        y += 28
        self.slider = make_slider(page, w - 24, group)
        self.slider.set_pos(8, y)
        self.slider.set_value(int(vehicle.lights.get("brightness", 0.85) * 100), 0)

        def _br(e):
            val = self.slider.get_value() / 100.0
            vehicle.lights["brightness"] = val
            theme.set_brightness(max(0.35, val))

        self.slider.add_event_cb(_br, lv.EVENT.VALUE_CHANGED, None)

        self.status = lv.label(page)
        self.status.set_style_text_color(theme.accent_lite(), 0)
        theme.apply_font(self.status, font)
        self.status.align(lv.ALIGN.BOTTOM_LEFT, 8, -6)
        self.update()

    def update(self):
        lit = [k for k, on in self.vehicle.lights.items() if on and k != "brightness"]
        self.status.set_text("Active: " + (", ".join(lit) if lit else "none"))


def build(page, vehicle, group, w=0, h=0):
    return LightsScreen(page, vehicle, group, w, h)
