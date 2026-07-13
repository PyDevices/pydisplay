# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""ColorPicker — compact RGB565 hue + SV picker."""

from eventsys import events

from .._constants import PAD
from ..widget import Widget


def _hsv_to_rgb565(h, s, v, color565):
    """h in [0,360), s/v in [0,1]; returns color via ``color565(r,g,b)``."""
    if s <= 0:
        c = int(v * 255)
        return color565(c, c, c)
    h = h % 360
    sector = h / 60.0
    i = int(sector)
    f = sector - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return color565(int(r * 255), int(g * 255), int(b * 255))


class ColorPicker(Widget):
    def __init__(  # noqa: PLR0913
        self,
        parent: Widget,
        x=0,
        y=0,
        w=None,
        h=None,
        align=None,
        align_to=None,
        fg=None,
        bg=None,
        visible=True,
        value=None,
        padding=None,
    ):
        """
        Compact picker: hue strip + SV region. ``value`` is a color565 int.
        """
        bg = bg if bg is not None else parent.color_theme.surface
        fg = fg if fg is not None else parent.color_theme.on_surface
        w = w or min(parent.width, 160)
        h = h or 100
        self._hue = 200.0
        self._sat = 0.6
        self._val = 0.8
        super().__init__(parent, x, y, w, h, align, align_to, fg, bg, visible, value, padding)
        if value is not None:
            self._value = value
        else:
            self._value = self._make_color()

    def _make_color(self):
        return _hsv_to_rgb565(self._hue, self._sat, self._val, self.display.pal.color565)

    def _register_callbacks(self):
        self.add_event_cb(events.MOUSEBUTTONDOWN, self._tap)
        self.add_event_cb(events.MOUSEMOTION, self._drag)

    def _hit(self, event):
        return self.display.translate_point(event.pos)

    def _tap(self, data=None, event=None):
        self._apply_point(*self._hit(event))

    def _drag(self, data=None, event=None):
        buttons = getattr(event, "buttons", 0) or 0
        if buttons:
            self._apply_point(*self._hit(event))

    def _apply_point(self, px, py):
        pa = self.padded_area
        strip_h = 14
        sv = type(pa)(pa.x, pa.y, pa.w, pa.h - strip_h - PAD)
        strip = type(pa)(pa.x, pa.y + pa.h - strip_h, pa.w, strip_h)
        if strip.contains(px, py):
            self._hue = 360.0 * (px - strip.x) / max(1, strip.w - 1)
        elif sv.contains(px, py):
            self._sat = (px - sv.x) / max(1, sv.w - 1)
            self._val = 1.0 - (py - sv.y) / max(1, sv.h - 1)
        else:
            return
        self.value = self._make_color()

    def draw(self, _=None):
        pa = self.padded_area
        strip_h = 14
        sv_h = pa.h - strip_h - PAD
        # SV region sample grid (coarse for MCU)
        step = 4
        for yy in range(0, sv_h, step):
            for xx in range(0, pa.w, step):
                s = xx / max(1, pa.w - 1)
                v = 1.0 - yy / max(1, sv_h - 1)
                c = _hsv_to_rgb565(self._hue, s, v, self.display.pal.color565)
                self.display.framebuf.fill_rect(pa.x + xx, pa.y + yy, step, step, c)
        # Hue strip
        sy = pa.y + sv_h + PAD
        for xx in range(0, pa.w, step):
            h = 360.0 * xx / max(1, pa.w - 1)
            c = _hsv_to_rgb565(h, 1.0, 1.0, self.display.pal.color565)
            self.display.framebuf.fill_rect(pa.x + xx, sy, step, strip_h, c)
        # Preview swatch
        sw = 16
        self.display.framebuf.fill_rect(pa.x + pa.w - sw - 2, pa.y + 2, sw, sw, self._value)
        self.display.framebuf.rect(
            pa.x + pa.w - sw - 2, pa.y + 2, sw, sw, self.color_theme.outline
        )
