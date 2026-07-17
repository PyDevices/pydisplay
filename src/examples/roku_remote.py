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

Possible additions in the future: jpg/png icons (ECP ``GET /query/icon/{id}``,
via ``RokuEngine.query_icon``) for APPS tiles / status.
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


def _xml_unescape(text):
    """Decode common XML entities in Roku app / device names."""
    if not text:
        return ""
    # &amp; first so later replacements are not double-processed.
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&apos;", "'")
    return text


def _ascii_label(text):
    """Unescape XML, then replace non-ASCII/control chars with spaces."""
    out = []
    for ch in _xml_unescape(text):
        o = ord(ch)
        out.append(ch if 32 <= o <= 126 else " ")
    return "".join(out)


def _wrap_label(text, max_chars, max_lines):
    """Wrap ``text`` into up to ``max_lines`` lines of ``max_chars`` each."""
    text = (text or "").strip()
    if max_chars < 1 or max_lines < 1:
        return [""]
    if not text:
        return [""]
    lines = []
    cur = ""
    for word in text.split(" "):
        if not word:
            continue
        while len(word) > max_chars:
            piece = word[:max_chars]
            word = word[max_chars:]
            if cur:
                lines.append(cur)
                cur = ""
                if len(lines) >= max_lines:
                    return lines
            if len(lines) + 1 >= max_lines and word:
                lines.append(piece[: max(1, max_chars - 1)] + ".")
                return lines
            lines.append(piece)
            if len(lines) >= max_lines:
                return lines
        trial = word if not cur else (cur + " " + word)
        if len(trial) <= max_chars:
            cur = trial
        else:
            lines.append(cur)
            if len(lines) >= max_lines:
                return lines
            cur = word
    if cur:
        if len(lines) < max_lines:
            lines.append(cur)
        else:
            # No room; mark overflow on the last line.
            last = lines[-1]
            if len(last) >= max_chars:
                lines[-1] = last[: max(1, max_chars - 1)] + "."
            else:
                lines[-1] = (last + ".")[:max_chars]
    return lines or [""]


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
    __slots__ = ("id", "label", "area", "role", "ecp", "meta", "round")

    def __init__(
        self, bid, label, x, y, w, h, role="key", ecp=None, meta=None, round=False
    ):
        self.id = bid
        self.label = label
        self.area = Area(x, y, w, h)
        self.role = role
        self.ecp = ecp
        self.meta = meta
        self.round = bool(round)


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
        self.app_page_size = 1
        self.discover_list = []
        self._status_line = "ready"
        self._dev_dump = ""

        # Layout regions
        self.status_h = max(28, self.FONT_H * self.font_scale + 2 * self.pad)
        self.margin_x = self.pad if not self.expanded else max(self.pad, self.width // 10)
        self.side_w = 0 if not self.expanded else max(36, self.width // 9)

        self.buttons = []
        self._by_id = {}
        self._status_timer = Timer(-1)
        self._pending_status = None
        self._playback_busy = False
        self._status_ticks = 0

        # Screen compose buffer — all drawing targets FrameBuffer; display_drv only presents.
        self.ba = bytearray(self.width * self.height * self.bpp)
        self.fb = FrameBuffer(self.ba, self.width, self.height, RGB565)
        max_w = self.width
        max_h = max(48, self.height // 8)
        self.btn_ba = bytearray(max_w * max_h * self.bpp)
        self.btn_fb = FrameBuffer(self.btn_ba, max_w, max_h, RGB565)

        # Discover before input handlers. Show the devices page and populate
        # buttons as each TV answers (progressive scan).
        self.page = "devices"
        self.discover_list = []
        self._status_line = "Scanning..."
        self._build_layout()
        self._draw_all()
        try:
            self._run_scan(seed_priority=False)
        except Exception as e:
            self._status_line = str(e)
            self._build_layout()
            self._draw_all()

        runtime.on(runtime.events.MOUSEBUTTONDOWN, self._on_mouse)
        runtime.on(runtime.events.KEYDOWN, self._on_key)
        # Soft pump: apply playback status from bg workers + periodic refresh.
        # Must not call Timer.deinit from this callback (librt deadlock).
        try:
            self._status_timer.init(
                mode=Timer.PERIODIC,
                period=250,
                callback=self._status_pump,
                hard=False,
            )
        except Exception:
            pass

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
        if self.page == "devices":
            self._layout_devices(content_x, y, content_w)
            return

        self._layout_remote(content_x, y, content_w)
        if self.expanded:
            self._layout_side_volume()
            self._layout_side_channel()

    def _add(
        self, bid, label, x, y, w, h, role="key", ecp=None, meta=None, round=False
    ):
        b = _Btn(
            bid,
            label,
            int(x),
            int(y),
            int(w),
            int(h),
            role=role,
            ecp=ecp,
            meta=meta,
            round=round,
        )
        self.buttons.append(b)
        self._by_id[bid] = b
        return b

    def _layout_remote(self, x0, y0, w):
        # Top utility row: Back | Home | Power (or Find on compact)
        row_h = max(36, self.height // 14)
        gap = self.pad
        n = 3
        bw = (w - gap * (n - 1)) // n
        # Power label reflects current TV state; press toggles On/Off.
        pwr_lab = "ON" if self.engine.power_is_on() else "OFF"
        labels = (
            ("back", "BACK", "Back", "key"),
            ("home", "HOME", "Home", "accent"),
            ("power", pwr_lab, None, "power"),
        )
        for i, (bid, lab, ecp, role) in enumerate(labels):
            self._add(bid, lab, x0 + i * (bw + gap), y0, bw, row_h, role=role, ecp=ecp)
        y = y0 + row_h + gap * 2

        # D-pad block (square-ish)
        dpad = min(w, max(140, self.height // 3))
        if dpad > w:
            dpad = w
        dx = x0 + (w - dpad) // 2
        cell = dpad // 3
        dpad_y = y
        # Up
        self._add("up", "^", dx + cell, dpad_y, cell, cell, role="dpad", ecp="Up")
        # Left / OK / Right
        self._add("left", "<", dx, dpad_y + cell, cell, cell, role="dpad", ecp="Left")
        self._add(
            "ok", "OK", dx + cell, dpad_y + cell, cell, cell, role="accent", ecp="Select"
        )
        self._add(
            "right", ">", dx + 2 * cell, dpad_y + cell, cell, cell, role="dpad", ecp="Right"
        )
        # Down
        self._add(
            "down", "v", dx + cell, dpad_y + 2 * cell, cell, cell, role="dpad", ecp="Down"
        )
        y = dpad_y + dpad + gap * 2

        # Smaller round BS / ENT: centered in the gutters between the content
        # border and the Left / Right D-pad buttons. Prefer the band above
        # REPLAY / SEARCH (pulled up half a height into the dpad gap when that
        # gap allows); otherwise the Left / OK / Right row.
        n = 3
        bw = (w - gap * (n - 1)) // n
        left_gutter = max(0, dx - x0)
        right_gutter = max(0, (x0 + w) - (dx + 3 * cell))
        if min(left_gutter, right_gutter) >= 18:
            side = max(18, min(row_h, (bw * 5) // 8, left_gutter, right_gutter))
            bs_x = x0 + (left_gutter - side) // 2
            ent_x = dx + 3 * cell + (right_gutter - side) // 2
        else:
            # D-pad is full-width; fall back to content-edge alignment.
            side = max(22, min(row_h, (bw * 5) // 8))
            bs_x = x0
            ent_x = x0 + w - side
        half = side // 2
        if gap * 2 >= half:
            sat_y = y - half
            y = sat_y + side + gap
        else:
            sat_y = dpad_y + cell + (cell - side) // 2
        self._add(
            "bs",
            "BS",
            bs_x,
            sat_y,
            side,
            side,
            role="key_alt",
            ecp="Backspace",
            round=True,
        )
        self._add(
            "enter_row",
            "ENT",
            ent_x,
            sat_y,
            side,
            side,
            role="key_alt",
            ecp="Enter",
            round=True,
        )
        # Captions (C): same band as BS/ENT, centered above mid-row Info (*).
        if self._captions_visible():
            cap_side = side
            mid_col_x = x0 + bw + gap
            cap_x = mid_col_x + (bw - cap_side) // 2
            cap_role = "accent" if self.engine.captions_track_hint() else "key_alt"
            self._add(
                "cap",
                "C",
                cap_x,
                sat_y,
                cap_side,
                cap_side,
                role=cap_role,
                ecp="ClosedCaption",
                round=True,
            )
        mid = (
            ("replay", "REPLAY", "InstantReplay", "key"),
            ("info", "*", "Info", "key"),
            ("search", "SRCH", "Search", "key"),
        )
        for i, (bid, lab, ecp, role) in enumerate(mid):
            self._add(bid, lab, x0 + i * (bw + gap), y, bw, row_h, role=role, ecp=ecp)
        y += row_h + gap * 2

        # Transport: Rev / Play / Fwd — Play label tracks media-player state.
        n = 3
        bw = (w - gap * (n - 1)) // n
        for i, (bid, lab, ecp) in enumerate(
            (
                ("rev", "<<", "Rev"),
                ("play", self._play_label(), "Play"),
                ("fwd", ">>", "Fwd"),
            )
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
                ("more_pg", "...", None, "ui"),
                ("find", "SCAN", None, "ui"),
            )
        n = len(labs)
        bw = (w - gap * (n - 1)) // n
        bh = max(32, row_h - 4)

        # Live TV / HDMI / AV (type=tvin): one row below transport when it fits
        # with chrome; otherwise skip (no new page).
        inputs = self.engine.inputs()
        ih = max(28, row_h - 6)
        y_in = y
        show_inputs = bool(inputs) and (y_in + ih + gap + bh <= self.height - self.pad)
        if show_inputs:
            n_in = len(inputs)
            ibw = (w - gap * (n_in - 1)) // n_in
            for i, app in enumerate(inputs):
                lab = self._input_short_label(app, max(2, ibw // 8))
                self._add(
                    "in_%d" % i,
                    lab,
                    x0 + i * (ibw + gap),
                    y_in,
                    ibw,
                    ih,
                    role="key_alt",
                    meta=app,
                )
            y_bot = y_in + ih + gap
        else:
            # Drop the chrome row by half a button height (keep inside the bezel).
            y_bot = min(y + bh // 2, self.height - self.pad - bh)

        for i, (bid, lab, ecp, role) in enumerate(labs):
            self._add(bid, lab, x0 + i * (bw + gap), y_bot, bw, bh, role=role, ecp=ecp)

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
        # Square tiles, 3 across; as many rows as fit below the chrome.
        cols = 3
        bw = (w - gap * (cols - 1)) // cols
        bh = bw
        avail_h = self.height - y - self.pad
        rows = max(1, (avail_h + gap) // (bh + gap))
        while rows > 1 and rows * bh + (rows - 1) * gap > avail_h:
            rows -= 1
        max_slots = rows * cols
        self.app_page_size = max_slots
        apps = self.engine.apps or []
        slice_apps = apps[self.app_offset : self.app_offset + max_slots]
        for i, app in enumerate(slice_apps):
            name = _ascii_label(app.get("name") or app.get("id") or "?")
            col = i % cols
            row = i // cols
            self._add(
                "app_%d" % i,
                name,
                x0 + col * (bw + gap),
                y + row * (bh + gap),
                bw,
                bh,
                role="accent" if i == 0 else "key",
                meta=app,
            )

    def _layout_devices(self, x0, y0, w):
        """Pick among discovered Rokus (friendly name only)."""
        row_h = max(36, self.height // 14)
        gap = self.pad
        self._add("back_pg", "REMOTE", x0, y0, w // 2 - gap, row_h, role="ui")
        self._add("find", "RESCAN", x0 + w // 2, y0, w // 2, row_h, role="accent")
        y = y0 + row_h + gap
        slot_h = max(32, self.FONT_H * self.font_scale + 2 * self.pad)
        devices = self.discover_list or []
        max_slots = max(1, (self.height - y - self.pad) // (slot_h + gap))
        for i, dev in enumerate(devices[:max_slots]):
            label = _ascii_label((dev.get("name") or "").strip() or "Roku")
            self._add(
                "dev_%d" % i,
                label,
                x0,
                y + i * (slot_h + gap),
                w,
                slot_h,
                role="accent" if i == 0 else "key",
                meta=dev,
            )

    def _layout_more(self, x0, y0, w):
        row_h = max(34, self.height // 16)
        gap = self.pad
        self._add("back_pg", "REMOTE", x0, y0, w // 2 - gap, row_h, role="ui")
        self._add("ip_pg", "IP", x0 + w // 2, y0, w // 2, row_h, role="ui")
        y = y0 + row_h + gap
        actions = (
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

    def _present(self):
        display_drv.blit_rect(self.ba, 0, 0, self.width, self.height)
        display_drv.show()

    def _draw_chassis(self):
        t = self.theme
        # Vertical gradient background
        h = self.height
        for j in range(h):
            c = _lerp(t["chassis"], t["chassis2"], j / (h - 1) if h > 1 else 0)
            self.fb.fill_rect(0, j, self.width, 1, c)
        # Inset bezel
        m = max(2, self.pad // 2)
        self.fb.rect(m, m, self.width - 2 * m, self.height - 2 * m, t["bezel"])

    def _draw_button(self, btn, pressed=False):
        x, y, w, h = btn.area.x, btn.area.y, btn.area.w, btn.area.h
        if w <= 0 or h <= 0:
            return
        # Cap scratch buffer; oversized keys draw straight onto the screen FB.
        if w * h * self.bpp > len(self.btn_ba):
            fg, face, lo, hi = self._role_colors(btn.role, pressed)
            self.fb.fill_rect(x, y, w, h, face)
            return

        fg, face, lo, hi = self._role_colors(btn.role, pressed)
        self.btn_fb = FrameBuffer(self.btn_ba, w, h, RGB565)
        self.btn_fb.fill(self.theme["chassis"])
        if btn.round:
            r = min(w, h) // 2
        else:
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

        text = btn.label or ""
        scale = self.font_scale
        pad = 2
        avail_w = max(1, w - 2 * pad)
        avail_h = max(1, h - 2 * pad)
        while scale > 1 and (
            self.FONT_W * scale > avail_w or self.FONT_H * scale > avail_h
        ):
            scale -= 1
        cw = self.FONT_W * scale
        ch = self.FONT_H * scale
        max_chars = max(1, avail_w // cw)
        max_lines = max(1, avail_h // ch)
        lines = _wrap_label(text, max_chars, max_lines)
        total_h = len(lines) * ch
        ty0 = max(0, (h - total_h) // 2)
        for li, line in enumerate(lines):
            tw = len(line) * cw
            tx = max(0, (w - tw) // 2)
            ty = ty0 + li * ch
            if scale != 1:
                self.btn_fb.text16(line, tx, ty, fg, scale)
            else:
                self.btn_fb.text16(line, tx, ty, fg)
        self.fb.blit(self.btn_fb, x, y)

    def _draw_status(self):
        t = self.theme
        y = self.pad
        x = self.pad
        w = self.width - 2 * self.pad
        h = self.status_h
        self.fb.fill_rect(x, y, w, h, t["status_bg"])
        self.fb.rect(x, y, w, h, t["bezel"])
        line = self._status_line or self.engine.status
        if self.page == "ip":
            line = "IP " + (self.ip_buf or "...")
        elif self.page == "more" and self._dev_dump:
            line = self._dev_dump[: max(8, w // (self.FONT_W * self.font_scale))]
        scale = self.font_scale
        max_chars = max(4, (w - 2 * self.pad) // (self.FONT_W * scale))
        if len(line) > max_chars:
            line = line[: max_chars - 1] + "."
        ty = max(0, y + (h - self.FONT_H * scale) // 2)
        if scale != 1:
            self.fb.text16(line, x + self.pad, ty, t["muted"], scale)
        else:
            self.fb.text16(line, x + self.pad, ty, t["muted"])

    def _draw_all(self):
        self._draw_chassis()
        self._draw_status()
        for btn in self.buttons:
            self._draw_button(btn, pressed=False)
        self._present()

    def _play_label(self):
        """Play-button text from media-player state: play / pause / neither."""
        state = ((self.engine.media_state or {}).get("state") or "").lower()
        if state in ("play", "buffer"):
            return "PAUSE"
        if state == "pause":
            return "PLAY"
        return "P/PA"

    def _captions_visible(self):
        """Show the captions C button while media is actively playing."""
        return bool(self.engine.media_active())

    def _input_short_label(self, app, max_chars=4):
        """Short ASCII label for a tvin input (TV / H1 / H2 / AV / …)."""
        aid = (app.get("id") or "").lower()
        name = _ascii_label(app.get("name") or "").strip()
        lab = ""
        if "dtv" in aid or "tuner" in aid or name.upper() in ("LIVE TV", "TV"):
            lab = "TV"
        elif "hdmi" in aid:
            for ch in aid:
                if ch.isdigit():
                    lab = "H" + ch
                    break
            if not lab:
                lab = "HDMI"
        elif "cvbs" in aid or "av" in aid:
            lab = "AV"
        elif name:
            # Prefer first word / digits hint from the friendly name.
            up = name.upper()
            if "HDMI" in up:
                for ch in up:
                    if ch.isdigit():
                        lab = "H" + ch
                        break
                if not lab:
                    lab = "HDMI"
            elif "TV" in up:
                lab = "TV"
            elif "AV" in up or "COMPOSITE" in up:
                lab = "AV"
            else:
                lab = name
        else:
            lab = aid.split(".")[-1] if aid else "?"
        lab = _ascii_label(lab).strip() or "?"
        if max_chars > 0 and len(lab) > max_chars:
            lab = lab[:max_chars]
        return lab

    def _sync_play_button(self):
        """Update the transport Play face when media state changes."""
        btn = self._by_id.get("play")
        if btn is None:
            return
        lab = self._play_label()
        if btn.label == lab:
            return
        btn.label = lab
        try:
            self._draw_button(btn, pressed=False)
            self._present()
        except Exception:
            pass

    def _sync_captions_button(self):
        """Show/hide or recolor the captions C button from media-player state."""
        want = self._captions_visible()
        btn = self._by_id.get("cap")
        if want and btn is None:
            # Layout needs the button; rebuild remote page once.
            if self.page == "remote":
                self._build_layout()
                self._draw_all()
            return
        if not want and btn is not None:
            if self.page == "remote":
                self._build_layout()
                self._draw_all()
            return
        if btn is None:
            return
        role = "accent" if self.engine.captions_track_hint() else "key_alt"
        if btn.role == role and btn.label == "C":
            return
        btn.role = role
        btn.label = "C"
        try:
            self._draw_button(btn, pressed=False)
            self._present()
        except Exception:
            pass

    def _refresh_status(self, line=None):
        """Redraw status band. Pass ``line`` to show a message; else playback status."""
        if line is None:
            line = self.engine.playback_status()
        self._status_line = _ascii_label(line)
        self._draw_status()
        self._present()
        if self.page == "remote":
            self._sync_play_button()
            self._sync_captions_button()

    def _queue_status(self, line):
        """Publish a status line for the soft status pump (safe from worker threads)."""
        self._pending_status = _ascii_label(line) if line is not None else None

    def _status_pump(self, _=None):
        """Drain pending status; periodically refresh playback on the remote page."""
        pending = self._pending_status
        if pending is not None:
            self._pending_status = None
            try:
                self._status_line = pending
                self._draw_status()
                if self.page == "remote":
                    self._sync_play_button()
                    self._sync_captions_button()
                self._present()
            except Exception:
                pass
        self._status_ticks += 1
        if (
            self.page == "remote"
            and self.engine.connected
            and self._status_ticks % 8 == 0
            and not self._playback_busy
        ):
            self._playback_busy = True

            def _work():
                try:
                    self._queue_status(self.engine.refresh_playback())
                except Exception:
                    pass
                self._playback_busy = False

            self._run_bg(_work)

    def _refresh_playback_bg(self, flash=None):
        """Background: refresh active-app/media-player and queue status."""
        if flash is not None:
            self._refresh_status(flash)

        def _work():
            try:
                self._queue_status(self.engine.refresh_playback())
            except Exception:
                pass

        self._run_bg(_work)

    # ----- interaction ----------------------------------------------------

    def _hit(self, pos):
        for btn in self.buttons:
            if btn.area.contains(pos):
                return btn
        return None

    def _flash(self, btn):
        """Draw pressed face. Caller restores via ``_unpress`` (no soft timer)."""
        self._draw_button(btn, pressed=True)
        self._present()

    def _unpress(self, bid):
        if bid and bid in self._by_id:
            self._draw_button(self._by_id[bid], pressed=False)
            self._present()

    def _run_bg(self, fn):
        """Run ``fn`` off the librt soft-timer delivery path when possible.

        Mouse handlers run inside the shared soft tick. Blocking ``urlopen``
        there often burns the full socket timeout (~5s); a worker keeps the UI
        snappy. Falls back to inline ``fn()`` when threads are unavailable.
        """
        try:
            import _thread

            _thread.start_new_thread(fn, ())
            return True
        except Exception:
            pass
        try:
            from concurrent.futures import ThreadPoolExecutor

            pool = getattr(self, "_bg_pool", None)
            if pool is None:
                self._bg_pool = ThreadPoolExecutor(max_workers=2)
                pool = self._bg_pool
            pool.submit(fn)
            return True
        except Exception:
            pass
        fn()
        return False

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
            self._refresh_status(ecp)

            def _press():
                self.engine.press(ecp)
                try:
                    self._queue_status(self.engine.refresh_playback())
                except Exception:
                    pass

            self._run_bg(_press)

    def _set_page(self, page):
        self.page = page
        self._build_layout()
        self._draw_all()

    def _refresh_apps(self):
        """Fetch the app list and show the apps page."""
        self.page = "apps"
        self.app_offset = 0
        self._status_line = "loading apps..."
        self._build_layout()
        self._draw_all()
        self.engine.query_apps()
        n = len(self.engine.apps or [])
        if n:
            self._status_line = "%d apps" % n
        else:
            self._status_line = self.engine.last_error or "no apps"
        self._build_layout()
        self._draw_all()

    def _on_device_found(self, dev):
        """Progressive UI: add a TV as soon as ECP confirms it."""
        host = (dev or {}).get("host") or ""
        if not host:
            return
        for existing in self.discover_list:
            if existing.get("host") == host:
                return
        self.discover_list.append(dev)
        # Don't yank the user back if they already opened a remote.
        if self.page != "devices":
            return
        self._status_line = "Scanning... %d" % len(self.discover_list)
        self._build_layout()
        self._draw_all()

    def _run_scan(self, seed_priority=True):
        """Clear list, show devices page, scan with progressive updates."""
        if seed_priority and self.discover_list:
            self.engine.discovered = list(self.discover_list)
        self.discover_list = []
        self.page = "devices"
        self._status_line = "Scanning..."
        self._build_layout()
        self._draw_all()
        devices = self.engine.discover(
            ssdp=False, scan_fallback=True, on_device=self._on_device_found
        )
        # Engine list is authoritative at end (may reorder); keep progressive list
        # if callback already filled it.
        if devices and len(devices) >= len(self.discover_list):
            self.discover_list = devices
        elif not self.discover_list:
            self.discover_list = devices or []
        if self.page != "devices":
            # User already picked a TV during progressive scan.
            return
        if not self.discover_list:
            self._refresh_status(self.engine.last_error or "no Roku found")
            self._build_layout()
            self._draw_all()
            return
        self._refresh_status("found %d - pick one" % len(self.discover_list))
        self._build_layout()
        self._draw_all()

    def _pick_device(self, dev):
        host = (dev or {}).get("host") or ""
        name = ((dev or {}).get("name") or "").strip() or host
        if not host:
            self._refresh_status("no host")
            return
        self.engine.set_host(host)
        self.ip_buf = host
        self.app_offset = 0
        # Jump to remote immediately, then finish ECP connect in the background of
        # this call (blocking HTTP, but UI already shows the remote).
        self.page = "remote"
        self._status_line = name
        self._build_layout()
        self._draw_all()
        self.engine.connect(discover_if_empty=False)
        # Rebuild so the power button shows ON/OFF from device-info.
        self._build_layout()
        self._draw_all()
        self._refresh_status(self.engine.playback_status())

    def _toggle_power(self):
        """Send PowerOn/PowerOff from current state; update the PWR face."""
        on = self.engine.power_is_on()
        key = "PowerOff" if on else "PowerOn"
        # Optimistic UI flip (ECP runs in the background).
        if not self.engine.device_info:
            self.engine.device_info = {}
        self.engine.device_info["power-mode"] = "DisplayOff" if on else "PowerOn"
        self._status_line = _ascii_label(key)
        if self.page == "remote":
            self._build_layout()
            self._draw_all()
        else:
            self._refresh_status(key)

        def _work():
            self.engine.press(key)
            try:
                self.engine.query_device_info()
                self._queue_status(self.engine.refresh_playback())
            except Exception:
                pass

        self._run_bg(_work)

    def _activate(self, btn):
        bid = btn.id
        # Brief pressed face, then restore BEFORE any work. Holding the pressed
        # look across blocking ECP HTTP made ~5s white buttons (socket timeout
        # under the librt soft-tick delivery path).
        skip_flash = bid == "find" or bid == "ip_ok" or bid.startswith("dev_")
        if not skip_flash:
            self._flash(btn)
            self._unpress(bid)
        self._activate_action(btn)

    def _activate_action(self, btn):
        bid = btn.id

        if bid == "theme":
            i = _THEME_NAMES.index(self.theme_name)
            self.theme_name = _THEME_NAMES[(i + 1) % len(_THEME_NAMES)]
            self.theme = _THEMES[self.theme_name]
            self._status_line = "theme: " + self.theme_name
            self._draw_all()
            return

        if bid == "power":
            self._toggle_power()
            return

        if bid == "apps_pg":
            self.page = "apps"
            self.app_offset = 0
            if not self.engine.apps:
                self._refresh_apps()
            else:
                self._status_line = "%d apps" % len(self.engine.apps)
                self._build_layout()
                self._draw_all()
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
            if self.engine.connected:
                self._refresh_playback_bg()
            return

        if bid.startswith("dev_") and btn.meta:
            self._pick_device(btn.meta)
            return

        if bid == "find":
            self._run_scan(seed_priority=True)
            return

        if bid == "apps_refresh":
            self._refresh_apps()
            return

        if bid == "apps_next":
            n = len(self.engine.apps)
            step = max(1, int(self.app_page_size or 1))
            if n:
                self.app_offset = (self.app_offset + step) % n
            self._build_layout()
            self._draw_all()
            return

        if bid.startswith("app_") and btn.meta:
            app = btn.meta
            app_id = app.get("id", "")
            name = app.get("name") or ""
            self._refresh_status("launch " + name)

            def _launch():
                self.engine.launch(app_id)
                try:
                    self._queue_status(self.engine.refresh_playback())
                except Exception:
                    pass

            self._run_bg(_launch)
            return

        if bid.startswith("in_") and btn.meta:
            app = btn.meta
            app_id = app.get("id", "")
            name = app.get("name") or app_id
            self._refresh_status("input " + _ascii_label(name))

            def _launch_in():
                self.engine.launch(app_id)
                try:
                    self._queue_status(self.engine.refresh_playback())
                except Exception:
                    pass

            self._run_bg(_launch_in)
            return

        if bid == "cap":
            self._refresh_status("ClosedCaption")

            def _cc():
                self.engine.press("ClosedCaption")
                try:
                    self._queue_status(self.engine.refresh_playback())
                except Exception:
                    pass

            self._run_bg(_cc)
            return

        if bid == "ip_clear":
            self.ip_buf = ""
            self._build_layout()
            self._draw_all()
            return

        if bid == "ip_ok":
            self.engine.set_host(self.ip_buf)
            self.app_offset = 0
            self.engine.connect(discover_if_empty=False)
            self._set_page("remote")
            self._refresh_status(self.engine.playback_status())
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
            self._refresh_status(self._dev_dump or self.engine.last_error or "no info")
            return

        if bid == "media":
            self._refresh_status(self.engine.refresh_playback() or "no media")
            return

        if bid == "tv_ch":
            raw = self.engine.query_tv_active_channel() or self.engine.query_tv_channels()
            self._dev_dump = (raw.replace("\n", " ")[:48]) if raw else "n/a"
            self._refresh_status(self._dev_dump)
            return

        if bid == "chanperf":
            raw = self.engine.query_chanperf()
            self._dev_dump = (raw.replace("\n", " ")[:48]) if raw else self.engine.last_error
            self._refresh_status(self._dev_dump or "perf n/a")
            return

        if btn.ecp:
            key = btn.ecp
            self._refresh_status(key)

            def _press():
                self.engine.press(key)
                try:
                    self._queue_status(self.engine.refresh_playback())
                except Exception:
                    pass

            self._run_bg(_press)
            return


remote = _Remote()
runtime.run_forever()
