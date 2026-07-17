# modules: roku_engine
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
roku_remote
====================================================
Museum-quality portrait Roku remote drawn with ``graphics.FrameBuffer``.

Shares :class:`roku_engine.RokuEngine` for ECP over the LAN (SSDP discover +
HTTP keypress / apps / queries). Uses only the four core pydisplay packages
(``graphics``, ``displaysys`` via ``board_config``, ``eventsys``, ``multimer``).

Geometry scales from a 320x480 reference up through tall phone portraits.
Compact layouts show classic remote chrome; expanded layouts add side volume,
channel / input shortcuts, theme picker, discover + IP entry, and an apps rail.

Edit ``ROKU_HOST`` below, or leave empty and use **Find** / Discover on device.
Requires Roku **Control by mobile apps → Enabled**. Join WiFi before running
on a microcontroller.
"""

import sys

_EXAMPLES = __file__.replace("\\", "/").rsplit("/", 1)[0]
if _EXAMPLES not in sys.path:
    sys.path.insert(0, _EXAMPLES)

from board_config import display_drv, runtime
from eventsys.keys import Keys
from graphics import RGB565, Area, FrameBuffer
from multimer import Timer
from roku_engine import ROKU_HOST as _DEFAULT_HOST
from roku_engine import RokuEngine

# Override here, or leave "" and use Discover / IP pad.
ROKU_HOST = _DEFAULT_HOST


def _c565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def _channels(c):
    return (c >> 8) & 0xF8, (c >> 3) & 0xFC, (c << 3) & 0xF8


def _lerp(c1, c2, t):
    r1, g1, b1 = _channels(c1)
    r2, g2, b2 = _channels(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return _c565(r, g, b)


def _shade(c, factor):
    """factor < 1 darkens, > 1 lightens (clamped)."""
    r, g, b = _channels(c)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return _c565(r, g, b)


# Named themes: professional chassis + key roles (no external palettes package).
_THEMES = {
    "midnight": {
        "chassis": _c565(0x12, 0x14, 0x1A),
        "chassis2": _c565(0x1A, 0x1E, 0x28),
        "bezel": _c565(0x0A, 0x0C, 0x10),
        "status_bg": _c565(0x1C, 0x22, 0x2E),
        "key": _c565(0x3A, 0x40, 0x4E),
        "key_alt": _c565(0x2E, 0x34, 0x40),
        "accent": _c565(0x7C, 0x5C, 0xFC),
        "accent2": _c565(0x5A, 0x3E, 0xD0),
        "power": _c565(0xE0, 0x5A, 0x4A),
        "transport": _c565(0x3A, 0x5A, 0x72),
        "text": _c565(0xF2, 0xF4, 0xF8),
        "muted": _c565(0x9A, 0xA0, 0xB0),
        "ok_text": _c565(0xFF, 0xFF, 0xFF),
        "press": _c565(0xE8, 0xEC, 0xF4),
        "press_text": _c565(0x18, 0x1A, 0x22),
    },
    "graphite": {
        "chassis": _c565(0x1A, 0x1A, 0x1C),
        "chassis2": _c565(0x28, 0x28, 0x2C),
        "bezel": _c565(0x0E, 0x0E, 0x10),
        "status_bg": _c565(0x24, 0x24, 0x28),
        "key": _c565(0x48, 0x48, 0x50),
        "key_alt": _c565(0x38, 0x38, 0x40),
        "accent": _c565(0x5A, 0xC8, 0xFA),
        "accent2": _c565(0x2E, 0x8A, 0xC0),
        "power": _c565(0xFF, 0x6B, 0x5A),
        "transport": _c565(0x50, 0x58, 0x68),
        "text": _c565(0xF5, 0xF5, 0xF7),
        "muted": _c565(0xA0, 0xA0, 0xA8),
        "ok_text": _c565(0x10, 0x12, 0x16),
        "press": _c565(0xFF, 0xFF, 0xFF),
        "press_text": _c565(0x20, 0x20, 0x24),
    },
    "ocean": {
        "chassis": _c565(0x0E, 0x1A, 0x22),
        "chassis2": _c565(0x14, 0x28, 0x34),
        "bezel": _c565(0x08, 0x12, 0x18),
        "status_bg": _c565(0x16, 0x2E, 0x3A),
        "key": _c565(0x2A, 0x4A, 0x58),
        "key_alt": _c565(0x22, 0x3C, 0x48),
        "accent": _c565(0x2E, 0xD2, 0xC0),
        "accent2": _c565(0x1A, 0xA0, 0x92),
        "power": _c565(0xF0, 0x70, 0x60),
        "transport": _c565(0x2A, 0x5A, 0x6E),
        "text": _c565(0xE8, 0xF4, 0xF8),
        "muted": _c565(0x8A, 0xB0, 0xBC),
        "ok_text": _c565(0x0A, 0x18, 0x1C),
        "press": _c565(0xD0, 0xF8, 0xF0),
        "press_text": _c565(0x0E, 0x1A, 0x22),
    },
    "ember": {
        "chassis": _c565(0x1A, 0x12, 0x10),
        "chassis2": _c565(0x28, 0x1A, 0x14),
        "bezel": _c565(0x10, 0x0A, 0x08),
        "status_bg": _c565(0x2A, 0x1C, 0x16),
        "key": _c565(0x4A, 0x36, 0x2C),
        "key_alt": _c565(0x3A, 0x2A, 0x22),
        "accent": _c565(0xFF, 0x9A, 0x3C),
        "accent2": _c565(0xD0, 0x6A, 0x20),
        "power": _c565(0xE0, 0x40, 0x40),
        "transport": _c565(0x5A, 0x40, 0x30),
        "text": _c565(0xFF, 0xF0, 0xE4),
        "muted": _c565(0xC0, 0xA0, 0x88),
        "ok_text": _c565(0x1A, 0x10, 0x0C),
        "press": _c565(0xFF, 0xE0, 0xC0),
        "press_text": _c565(0x2A, 0x16, 0x10),
    },
}
_THEME_NAMES = ("midnight", "graphite", "ocean", "ember")


class _Btn:
    __slots__ = ("id", "label", "area", "role", "ecp", "meta")

    def __init__(self, bid, label, x, y, w, h, role="key", ecp=None, meta=None):
        self.id = bid
        self.label = label
        self.area = Area(x, y, w, h)
        self.role = role
        self.ecp = ecp
        self.meta = meta


class _Remote:
    FONT_W = 8
    FONT_H = 16

    def __init__(self):
        self.width = display_drv.width
        self.height = display_drv.height
        self.bpp = display_drv.color_depth // 8
        self.unit = min(self.width, self.height)
        self.expanded = self.height >= 640 or (self.height >= 560 and self.unit >= 360)

        self.pad = max(3, self.unit // 64)
        self.radius = max(5, self.unit // 36)
        self.font_scale = max(1, self.unit // 280)
        self.title_scale = self.font_scale + (1 if self.unit >= 400 else 0)

        self.theme_name = "midnight"
        self.theme = _THEMES[self.theme_name]
        self.engine = RokuEngine(host=ROKU_HOST)
        self.ip_buf = self.engine.host or ""
        self.page = "remote"  # remote | apps | more | ip
        self.app_offset = 0
        self.discover_list = []
        self._status_line = "ready"
        self._dev_dump = ""

        # Layout regions
        self.status_h = max(28, self.FONT_H * self.font_scale + 2 * self.pad)
        self.margin_x = self.pad if not self.expanded else max(self.pad, self.width // 10)
        self.side_w = 0 if not self.expanded else max(36, self.width // 9)

        self.buttons = []
        self._by_id = {}
        self._pressed_id = None
        self._release_timer = Timer(-1)
        self._status_timer = Timer(-1)

        max_w = self.width
        max_h = max(48, self.height // 8)
        self.btn_ba = bytearray(max_w * max_h * self.bpp)
        self.btn_fb = FrameBuffer(self.btn_ba, max_w, max_h, RGB565)

        self._build_layout()
        self._draw_all()

        runtime.on(runtime.events.MOUSEBUTTONDOWN, self._on_mouse)
        runtime.on(runtime.events.KEYDOWN, self._on_key)

        # Best-effort connect (may fail offline — UI still usable).
        try:
            if self.engine.host:
                self.engine.connect(discover_if_empty=False)
                self._status_line = self.engine.status
                self._refresh_status()
        except Exception as e:
            self._status_line = str(e)
            self._refresh_status()

    # ----- layout ---------------------------------------------------------

    def _build_layout(self):
        self.buttons = []
        self._by_id = {}
        y = self.pad
        # Status band is drawn separately; reserve space.
        y += self.status_h + self.pad

        content_x = self.margin_x
        content_w = self.width - 2 * self.margin_x
        if self.expanded:
            content_x = self.margin_x + self.side_w + self.pad
            content_w = self.width - content_x - self.margin_x - self.side_w - self.pad

        if self.page == "ip":
            self._layout_ip(content_x, y, content_w)
            return
        if self.page == "apps":
            self._layout_apps(content_x, y, content_w)
            return
        if self.page == "more":
            self._layout_more(content_x, y, content_w)
            return

        self._layout_remote(content_x, y, content_w)
        if self.expanded:
            self._layout_side_volume()
            self._layout_side_channel()

    def _add(self, bid, label, x, y, w, h, role="key", ecp=None, meta=None):
        b = _Btn(bid, label, int(x), int(y), int(w), int(h), role=role, ecp=ecp, meta=meta)
        self.buttons.append(b)
        self._by_id[bid] = b
        return b

    def _layout_remote(self, x0, y0, w):
        # Top utility row: Back | Home | Power (or Find on compact)
        row_h = max(36, self.height // 14)
        gap = self.pad
        n = 3
        bw = (w - gap * (n - 1)) // n
        labels = (("back", "BACK", "Back"), ("home", "HOME", "Home"), ("power", "PWR", "PowerOff"))
        for i, (bid, lab, ecp) in enumerate(labels):
            role = "accent" if bid == "home" else ("power" if bid == "power" else "key")
            self._add(bid, lab, x0 + i * (bw + gap), y0, bw, row_h, role=role, ecp=ecp)
        y = y0 + row_h + gap * 2

        # D-pad block (square-ish)
        dpad = min(w, max(140, self.height // 3))
        if dpad > w:
            dpad = w
        dx = x0 + (w - dpad) // 2
        cell = dpad // 3
        # Up
        self._add("up", "^", dx + cell, y, cell, cell, role="dpad", ecp="Up")
        # Left / OK / Right
        self._add("left", "<", dx, y + cell, cell, cell, role="dpad", ecp="Left")
        self._add("ok", "OK", dx + cell, y + cell, cell, cell, role="accent", ecp="Select")
        self._add("right", ">", dx + 2 * cell, y + cell, cell, cell, role="dpad", ecp="Right")
        # Down
        self._add("down", "v", dx + cell, y + 2 * cell, cell, cell, role="dpad", ecp="Down")
        y += dpad + gap * 2

        # Replay / Info / Options(*) / Search
        n = 4
        bw = (w - gap * (n - 1)) // n
        # Classic remote: Instant Replay, Info (*), Search (voice), Enter
        mid = (
            ("replay", "REPLAY", "InstantReplay", "key"),
            ("info", "*", "Info", "key"),
            ("search", "SRCH", "Search", "key"),
            ("enter_row", "ENTER", "Enter", "key_alt"),
        )
        for i, (bid, lab, ecp, role) in enumerate(mid):
            self._add(bid, lab, x0 + i * (bw + gap), y, bw, row_h, role=role, ecp=ecp)
        y += row_h + gap * 2

        # Transport: Rev / Play / Fwd
        n = 3
        bw = (w - gap * (n - 1)) // n
        for i, (bid, lab, ecp) in enumerate(
            (("rev", "<<", "Rev"), ("play", "PLAY", "Play"), ("fwd", ">>", "Fwd"))
        ):
            self._add(bid, lab, x0 + i * (bw + gap), y, bw, row_h, role="transport", ecp=ecp)
        y += row_h + gap * 2

        # Bottom chrome: theme / apps / more / discover(+ip)
        if self.expanded:
            labs = (
                ("theme", "THEME", None, "ui"),
                ("apps_pg", "APPS", None, "ui"),
                ("more_pg", "MORE", None, "ui"),
                ("find", "SCAN", None, "ui"),
            )
        else:
            labs = (
                ("theme", "THM", None, "ui"),
                ("apps_pg", "APP", None, "ui"),
                ("more_pg", "…", None, "ui"),
                ("find", "SCAN", None, "ui"),
            )
        n = len(labs)
        bw = (w - gap * (n - 1)) // n
        bh = max(32, row_h - 4)
        for i, (bid, lab, ecp, role) in enumerate(labs):
            self._add(bid, lab, x0 + i * (bw + gap), y, bw, bh, role=role, ecp=ecp)

        # Expanded: input shortcuts under bottom row if room
        y2 = y + bh + gap
        if self.expanded and y2 + row_h < self.height - self.pad:
            inputs = (
                ("tuner", "TV", "InputTuner"),
                ("hdmi1", "H1", "InputHDMI1"),
                ("hdmi2", "H2", "InputHDMI2"),
                ("hdmi3", "H3", "InputHDMI3"),
                ("av", "AV", "InputAV1"),
            )
            n = len(inputs)
            bw = (w - gap * (n - 1)) // n
            for i, (bid, lab, ecp) in enumerate(inputs):
                self._add(bid, lab, x0 + i * (bw + gap), y2, bw, row_h - 4, role="key_alt", ecp=ecp)

    def _layout_side_volume(self):
        x = self.margin_x
        top = self.pad + self.status_h + self.pad
        bottom = self.height - self.pad
        h = bottom - top
        # Volume rocker: Up / Mute / Down stacked
        seg = h // 3
        self._add("vol_up", "+", x, top, self.side_w, seg - self.pad, role="transport", ecp="VolumeUp")
        self._add(
            "vol_mute",
            "M",
            x,
            top + seg,
            self.side_w,
            seg - self.pad,
            role="key_alt",
            ecp="VolumeMute",
        )
        self._add(
            "vol_dn",
            "-",
            x,
            top + 2 * seg,
            self.side_w,
            seg - self.pad,
            role="transport",
            ecp="VolumeDown",
        )

    def _layout_side_channel(self):
        x = self.width - self.margin_x - self.side_w
        top = self.pad + self.status_h + self.pad
        bottom = self.height - self.pad
        h = bottom - top
        seg = h // 3
        self._add("ch_up", "CH+", x, top, self.side_w, seg - self.pad, role="key", ecp="ChannelUp")
        self._add(
            "enter",
            "ENT",
            x,
            top + seg,
            self.side_w,
            seg - self.pad,
            role="key_alt",
            ecp="Enter",
        )
        self._add(
            "ch_dn",
            "CH-",
            x,
            top + 2 * seg,
            self.side_w,
            seg - self.pad,
            role="key",
            ecp="ChannelDown",
        )

    def _layout_apps(self, x0, y0, w):
        row_h = max(36, self.height // 14)
        gap = self.pad
        self._add("back_pg", "REMOTE", x0, y0, w // 3 - gap, row_h, role="ui")
        self._add("apps_refresh", "REFRESH", x0 + w // 3, y0, w // 3 - gap, row_h, role="ui")
        self._add("apps_next", "NEXT", x0 + 2 * w // 3, y0, w // 3, row_h, role="ui")
        y = y0 + row_h + gap
        # App list slots
        slot_h = max(32, self.FONT_H * self.font_scale + 2 * self.pad)
        apps = self.engine.apps or []
        max_slots = max(1, (self.height - y - self.pad) // (slot_h + gap))
        slice_apps = apps[self.app_offset : self.app_offset + max_slots]
        if not slice_apps:
            self._add("apps_empty", "(no apps — REFRESH)", x0, y, w, slot_h, role="key_alt")
            return
        for i, app in enumerate(slice_apps):
            name = app.get("name") or app.get("id") or "?"
            if len(name) > 18:
                name = name[:17] + "."
            self._add(
                "app_%d" % i,
                name,
                x0,
                y + i * (slot_h + gap),
                w,
                slot_h,
                role="accent" if i == 0 else "key",
                meta=app,
            )

    def _layout_more(self, x0, y0, w):
        row_h = max(34, self.height // 16)
        gap = self.pad
        self._add("back_pg", "REMOTE", x0, y0, w // 2 - gap, row_h, role="ui")
        self._add("ip_pg", "IP", x0 + w // 2, y0, w // 2, row_h, role="ui")
        y = y0 + row_h + gap
        actions = (
            ("find_remote", "FIND REMOTE", "FindRemote"),
            ("bs", "BACKSPACE", "Backspace"),
            ("enter_k", "ENTER", "Enter"),
            ("replay2", "REPLAY", "InstantReplay"),
            ("dev_info", "DEV INFO", None),
            ("media", "MEDIA", None),
            ("tv_ch", "TV CH", None),
            ("chanperf", "PERF", None),
        )
        cols = 2
        bw = (w - gap) // cols
        for i, (bid, lab, ecp) in enumerate(actions):
            col = i % cols
            row = i // cols
            role = "ui" if ecp is None else "key"
            self._add(
                bid,
                lab,
                x0 + col * (bw + gap),
                y + row * (row_h + gap),
                bw,
                row_h,
                role=role,
                ecp=ecp,
            )

    def _layout_ip(self, x0, y0, w):
        row_h = max(34, self.height // 14)
        gap = self.pad
        self._add("back_pg", "BACK", x0, y0, w // 3 - gap, row_h, role="ui")
        self._add("ip_clear", "CLR", x0 + w // 3, y0, w // 3 - gap, row_h, role="ui")
        self._add("ip_ok", "SET", x0 + 2 * w // 3, y0, w // 3, row_h, role="accent")
        y = y0 + row_h + gap
        # Display current IP buffer as a fake label button
        shown = self.ip_buf if self.ip_buf else "(empty)"
        self._add("ip_disp", shown, x0, y, w, row_h, role="key_alt")
        y += row_h + gap
        keys = "123456789.0<"
        cols = 3
        bw = (w - gap * (cols - 1)) // cols
        bh = row_h
        for i, ch in enumerate(keys):
            col = i % cols
            row = i // cols
            lab = "BS" if ch == "<" else ch
            self._add(
                "ipk_%d" % i,
                lab,
                x0 + col * (bw + gap),
                y + row * (bh + gap),
                bw,
                bh,
                role="key",
                meta=ch,
            )
        y2 = y + 4 * (bh + gap)
        if y2 + row_h < self.height - self.pad:
            self._add("find", "DISCOVER", x0, y2, w, row_h, role="accent")

    # ----- drawing --------------------------------------------------------

    def _role_colors(self, role, pressed=False):
        t = self.theme
        if pressed:
            return t["press_text"], t["press"], _shade(t["press"], 0.85), _shade(t["press"], 1.08)
        if role == "accent":
            face = t["accent"]
            return t["ok_text"], face, t["accent2"], _shade(face, 1.15)
        if role == "power":
            face = t["power"]
            return t["text"], face, _shade(face, 0.75), _shade(face, 1.12)
        if role == "transport":
            face = t["transport"]
            return t["text"], face, _shade(face, 0.8), _shade(face, 1.12)
        if role == "dpad":
            face = t["key"]
            return t["text"], face, _shade(face, 0.78), _shade(face, 1.14)
        if role == "ui":
            face = t["key_alt"]
            return t["muted"], face, _shade(face, 0.8), _shade(face, 1.1)
        if role == "key_alt":
            face = t["key_alt"]
            return t["text"], face, _shade(face, 0.8), _shade(face, 1.1)
        face = t["key"]
        return t["text"], face, _shade(face, 0.78), _shade(face, 1.12)

    def _draw_chassis(self):
        t = self.theme
        # Vertical gradient background
        h = self.height
        for j in range(h):
            c = _lerp(t["chassis"], t["chassis2"], j / (h - 1) if h > 1 else 0)
            display_drv.fill_rect(0, j, self.width, 1, c)
        # Inset bezel
        m = max(2, self.pad // 2)
        display_drv.rect(m, m, self.width - 2 * m, self.height - 2 * m, t["bezel"])

    def _draw_button(self, btn, pressed=False):
        x, y, w, h = btn.area.x, btn.area.y, btn.area.w, btn.area.h
        if w <= 0 or h <= 0:
            return
        # Cap buffer use
        if w * h * self.bpp > len(self.btn_ba):
            # draw simplified fill without offscreen if too large
            fg, face, lo, hi = self._role_colors(btn.role, pressed)
            display_drv.fill_rect(x, y, w, h, face)
            return

        fg, face, lo, hi = self._role_colors(btn.role, pressed)
        self.btn_fb = FrameBuffer(self.btn_ba, w, h, RGB565)
        self.btn_fb.fill(self.theme["chassis"])
        r = min(self.radius, w // 3, h // 3)

        # 3D: top-lit gradient round rect
        for j in range(h):
            if j < r:
                d = r - j
            elif j >= h - r:
                d = r - (h - 1 - j)
            else:
                d = 0
            if d:
                # approximate circular inset
                inset = 0
                rr = r * r
                dd = d * d
                # integer sqrt-ish: try
                s = 0
                while (s + 1) * (s + 1) <= rr - dd:
                    s += 1
                inset = r - s
            else:
                inset = 0
            t = j / (h - 1) if h > 1 else 0
            # pressed → invert lighting
            if pressed:
                c = _lerp(lo, hi, t)
            else:
                c = _lerp(hi, lo, t)
            ww = w - 2 * inset
            if ww > 0:
                self.btn_fb.fill_rect(inset, j, ww, 1, c)

        # Soft rim
        self.btn_fb.round_rect(0, 0, w, h, r, _shade(face, 0.55), False)

        text = btn.label
        scale = self.font_scale
        while scale > 1 and len(text) * self.FONT_W * scale > w - 4:
            scale -= 1
        tw = len(text) * self.FONT_W * scale
        th = self.FONT_H * scale
        tx = max(0, (w - tw) // 2)
        ty = max(0, (h - th) // 2)
        if scale != 1:
            self.btn_fb.text16(text, tx, ty, fg, scale)
        else:
            self.btn_fb.text16(text, tx, ty, fg)
        display_drv.blit_rect(self.btn_ba[: w * h * self.bpp], x, y, w, h)

    def _draw_status(self):
        t = self.theme
        y = self.pad
        x = self.pad
        w = self.width - 2 * self.pad
        h = self.status_h
        display_drv.fill_rect(x, y, w, h, t["status_bg"])
        display_drv.rect(x, y, w, h, t["bezel"])
        line = self._status_line or self.engine.status
        if self.page == "ip":
            line = "IP " + (self.ip_buf or "…")
        elif self.page == "more" and self._dev_dump:
            line = self._dev_dump[: max(8, w // (self.FONT_W * self.font_scale))]
        scale = self.font_scale
        max_chars = max(4, (w - 2 * self.pad) // (self.FONT_W * scale))
        if len(line) > max_chars:
            line = line[: max_chars - 1] + "."
        # Use scratch for text band
        if w * h * self.bpp <= len(self.btn_ba):
            self.btn_fb = FrameBuffer(self.btn_ba, w, h, RGB565)
            self.btn_fb.fill(t["status_bg"])
            ty = max(0, (h - self.FONT_H * scale) // 2)
            if scale != 1:
                self.btn_fb.text16(line, self.pad, ty, t["muted"], scale)
            else:
                self.btn_fb.text16(line, self.pad, ty, t["muted"])
            display_drv.blit_rect(self.btn_ba[: w * h * self.bpp], x, y, w, h)
        else:
            display_drv.fill_rect(x, y, w, h, t["status_bg"])

    def _draw_all(self):
        self._draw_chassis()
        self._draw_status()
        for btn in self.buttons:
            self._draw_button(btn, pressed=False)
        display_drv.show()

    def _refresh_status(self):
        self._status_line = self.engine.status
        self._draw_status()
        display_drv.show()

    # ----- interaction ----------------------------------------------------

    def _hit(self, pos):
        for btn in self.buttons:
            if btn.area.contains(pos):
                return btn
        return None

    def _flash(self, btn):
        self._pressed_id = btn.id
        self._draw_button(btn, pressed=True)
        display_drv.show()
        self._release_timer.init(mode=Timer.ONE_SHOT, period=120, callback=self._release)

    def _release(self, _=None):
        bid = self._pressed_id
        self._pressed_id = None
        if bid and bid in self._by_id:
            self._draw_button(self._by_id[bid], pressed=False)
            display_drv.show()

    def _on_mouse(self, e):
        btn = self._hit(e.pos)
        if btn is None:
            return
        self._activate(btn)

    def _on_key(self, e):
        key = e.key
        mapping = {
            Keys.K_UP: "Up",
            Keys.K_DOWN: "Down",
            Keys.K_LEFT: "Left",
            Keys.K_RIGHT: "Right",
            Keys.K_RETURN: "Select",
            Keys.K_KP_ENTER: "Select",
            Keys.K_ESCAPE: "Back",
            Keys.K_BACKSPACE: "Backspace",
            Keys.K_h: "Home",
            Keys.K_i: "Info",
            Keys.K_SPACE: "Play",
        }
        ecp = mapping.get(key)
        if ecp:
            self.engine.press(ecp)
            self._status_line = self.engine.status
            self._refresh_status()

    def _set_page(self, page):
        self.page = page
        self._build_layout()
        self._draw_all()

    def _activate(self, btn):
        self._flash(btn)
        bid = btn.id

        if bid == "theme":
            i = _THEME_NAMES.index(self.theme_name)
            self.theme_name = _THEME_NAMES[(i + 1) % len(_THEME_NAMES)]
            self.theme = _THEMES[self.theme_name]
            self._status_line = "theme: " + self.theme_name
            self._draw_all()
            return

        if bid == "apps_pg":
            self._set_page("apps")
            return
        if bid == "more_pg":
            self._set_page("more")
            return
        if bid == "ip_pg":
            self.ip_buf = self.engine.host or self.ip_buf
            self._set_page("ip")
            return
        if bid == "back_pg":
            self._set_page("remote")
            return

        if bid == "find":
            self._status_line = "scanning…"
            self._refresh_status()
            devices = self.engine.discover(timeout=2.5)
            self.discover_list = devices
            if devices:
                self.engine.set_host(devices[0]["host"])
                self.ip_buf = self.engine.host
                self.engine.connect(discover_if_empty=False)
                self._status_line = "found %d · %s" % (len(devices), self.engine.status)
            else:
                self._status_line = self.engine.last_error or "no Roku found"
            if self.page == "ip":
                self._build_layout()
                self._draw_all()
            else:
                self._refresh_status()
            return

        if bid == "apps_refresh":
            self.engine.query_apps()
            self.app_offset = 0
            self._status_line = "%d apps" % len(self.engine.apps)
            self._build_layout()
            self._draw_all()
            return

        if bid == "apps_next":
            n = len(self.engine.apps)
            if n:
                self.app_offset = (self.app_offset + 4) % n
            self._build_layout()
            self._draw_all()
            return

        if bid.startswith("app_") and btn.meta:
            app = btn.meta
            ok = self.engine.launch(app.get("id", ""))
            self._status_line = ("launched " if ok else "fail ") + (app.get("name") or "")
            try:
                self.engine.query_active_app()
            except Exception:
                pass
            self._refresh_status()
            return

        if bid == "ip_clear":
            self.ip_buf = ""
            self._build_layout()
            self._draw_all()
            return

        if bid == "ip_ok":
            self.engine.set_host(self.ip_buf)
            self.engine.connect(discover_if_empty=False)
            self._status_line = self.engine.status
            self._set_page("remote")
            return

        if bid.startswith("ipk_") and btn.meta is not None:
            ch = btn.meta
            if ch == "<":
                self.ip_buf = self.ip_buf[:-1]
            else:
                if len(self.ip_buf) < 15:
                    self.ip_buf += ch
            self._build_layout()
            self._draw_all()
            return

        if bid == "dev_info":
            info = self.engine.query_device_info()
            self._dev_dump = info.get("model-name", "") + " " + info.get("power-mode", "")
            self._status_line = self._dev_dump or self.engine.last_error or "no info"
            self._refresh_status()
            return

        if bid == "media":
            raw = self.engine.query_media_player()
            self._dev_dump = (raw.replace("\n", " ")[:48]) if raw else "no media"
            self._status_line = self._dev_dump
            self._refresh_status()
            return

        if bid == "tv_ch":
            raw = self.engine.query_tv_active_channel() or self.engine.query_tv_channels()
            self._dev_dump = (raw.replace("\n", " ")[:48]) if raw else "n/a"
            self._status_line = self._dev_dump
            self._refresh_status()
            return

        if bid == "chanperf":
            raw = self.engine.query_chanperf()
            self._dev_dump = (raw.replace("\n", " ")[:48]) if raw else self.engine.last_error
            self._status_line = self._dev_dump or "perf n/a"
            self._refresh_status()
            return

        if btn.ecp:
            self.engine.press(btn.ecp)
            if btn.ecp in ("Home", "Select", "Launch"):
                try:
                    self.engine.query_active_app()
                except Exception:
                    pass
            self._status_line = self.engine.status
            self._refresh_status()


remote = _Remote()
runtime.run_forever()
