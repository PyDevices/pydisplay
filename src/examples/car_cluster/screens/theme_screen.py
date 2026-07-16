# SPDX-License-Identifier: MIT
"""Color scheme, chrome shininess, and gauge sizing."""

import lvgl as lv

import theme
from screens._common import content_size, make_button, make_slider, prep_page, section_label, zero_pad


class ThemeScreen:
    def __init__(self, page, vehicle, group, w=0, h=0):
        self.vehicle = vehicle
        w, h = content_size(prep_page(page, w, h), w, h)
        font = theme.pick_font(200, page)
        self._sliders = []

        section_label(page, "COLOR SCHEME", 4, accent=True)
        self.scheme_lbl = lv.label(page)
        self.scheme_lbl.set_style_text_color(theme.accent_lite(), 0)
        theme.apply_font(self.scheme_lbl, theme.pick_font(240, page))
        zero_pad(self.scheme_lbl)
        self.scheme_lbl.set_pos(8, 36)

        prev_b = make_button(page, "PREV", 96, 38, group)
        next_b = make_button(page, "NEXT", 96, 38, group)
        prev_b.set_pos(8, 72)
        next_b.set_pos(112, 72)

        def _prev(e):
            theme.set_scheme(theme.scheme_index() - 1)

        def _next(e):
            theme.set_scheme(theme.scheme_index() + 1)

        prev_b.add_event_cb(_prev, lv.EVENT.CLICKED, None)
        next_b.add_event_cb(_next, lv.EVENT.CLICKED, None)

        y = 128
        controls = (
            ("Chrome shininess", theme.shininess, theme.set_shininess),
            (
                "Gauge sizing",
                lambda: (theme.gauge_scale() - 0.85) / 0.30,
                lambda t: theme.set_gauge_scale(0.85 + t * 0.30),
            ),
            ("Brightness", theme.brightness, theme.set_brightness),
        )
        for label, getter, setter in controls:
            section_label(page, label.upper(), y)
            y += 26
            sl = make_slider(page, w - 24, group)
            sl.set_pos(8, y)
            sl.set_range(0, 100)
            sl.set_value(int(getter() * 100), 0)
            self._sliders.append(sl)

            def _bind(slider, setter_fn):
                def _cb(e):
                    setter_fn(slider.get_value() / 100.0)

                return _cb

            sl.add_event_cb(_bind(sl, setter), lv.EVENT.VALUE_CHANGED, None)
            y += 52

        self.hint = lv.label(page)
        self.hint.set_text("PREV/NEXT changes Material accent across gauges and rails.")
        self.hint.set_style_text_color(theme.text_dim(), 0)
        theme.apply_font(self.hint, font)
        zero_pad(self.hint)
        self.hint.align(lv.ALIGN.BOTTOM_LEFT, 8, -6)
        self.apply_theme()

    def apply_theme(self):
        self.scheme_lbl.set_text(
            "%s  (%d/%d)" % (theme.scheme_name(), theme.scheme_index() + 1, theme.scheme_count())
        )
        self.scheme_lbl.set_style_text_color(theme.accent_lite(), 0)
        # Restyle slider fills / knobs to the new accent
        for sl in self._sliders:
            sl.set_style_bg_color(theme.accent(), lv.PART.INDICATOR)
            sl.set_style_bg_color(theme.accent_lite(), lv.PART.KNOB)

    def update(self):
        # Scheme label only — avoid restyling all sliders every vehicle tick.
        self.scheme_lbl.set_text(
            "%s  (%d/%d)" % (theme.scheme_name(), theme.scheme_index() + 1, theme.scheme_count())
        )


def build(page, vehicle, group, w=0, h=0):
    return ThemeScreen(page, vehicle, group, w, h)
