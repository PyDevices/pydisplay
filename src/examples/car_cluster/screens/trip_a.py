# SPDX-License-Identifier: MIT
"""Trip computer A."""

import lvgl as lv

import theme
from screens._common import content_size, kv_row, make_button, prep_page, spread_rows


class TripScreen:
    which = "a"
    title = "TRIP A"

    def __init__(self, page, vehicle, group, w=0, h=0):
        self.vehicle = vehicle
        w, h = content_size(prep_page(page, w, h), w, h)

        labels = ("Distance", "Avg speed", "Avg MPG", "Elapsed", "Max speed")
        ys = spread_rows(len(labels), top=12, bottom=52, height=h)
        self.rows = []
        for lab, y in zip(labels, ys):
            _k, v = kv_row(page, y, lab, "--", w)
            self.rows.append(v)

        self.reset = make_button(page, "RESET TRIP", min(180, w - 24), 40, group)
        self.reset.align(lv.ALIGN.BOTTOM_MID, 0, -8)

        which = self.which

        def _reset(e):
            vehicle.reset_trip(which)

        self.reset.add_event_cb(_reset, lv.EVENT.CLICKED, None)
        self.update()

    def update(self):
        v = self.vehicle
        trip = v.trip_a if self.which == "a" else v.trip_b
        mins = int(trip["time_s"] // 60)
        secs = int(trip["time_s"] % 60)
        vals = (
            "%.1f mi" % trip["distance"],
            "%.1f mph" % v.trip_avg_speed(self.which),
            "%.1f" % v.trip_mpg(self.which),
            "%d:%02d" % (mins, secs),
            "%.0f mph" % trip["max_speed"],
        )
        for lbl, text in zip(self.rows, vals):
            lbl.set_text(text)


def build(page, vehicle, group, w=0, h=0):
    return TripScreen(page, vehicle, group, w, h)
