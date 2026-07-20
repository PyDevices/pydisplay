# deps: lvgl
# modules: roku_engine
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
roku_lvgl
====================================================
Museum-quality Roku remote built with LVGL.

The flagship of three interchangeable Roku front ends (``roku_graphics``,
``roku_widgets``, ``roku_lvgl``); ``roku_remote`` launches this one. All three
drive the same :class:`roku_engine.RokuEngine`, so the display layer is fully
replaceable.

Design: a deep charcoal chassis with a single violet accent, a brushed status
"plaque", a circular D-pad cluster, a refined transport bar, and slim side
volume / channel columns on wider panels. Geometry derives from
``display_drv.width`` / ``height`` so it scales from 320x480 phones up through
desktop windows.

Import order matters: ``display_driver`` must be imported after ``board_config``
so LVGL's display / input devices are wired before widgets are created. Blocking
ECP calls run on a worker thread; because LVGL is not re-entrant, the worker only
touches the engine and sets mailbox flags, and an ``lv.timer`` applies every
widget change on the LVGL (main) thread.

Edit ``ROKU_HOST`` below, or leave empty and use SCAN / the IP pad on device.
Requires Roku **Control by mobile apps -> Enabled**. Join WiFi before running
on a microcontroller.
"""

import sys

_EXAMPLES = __file__.replace("\\", "/").rsplit("/", 1)[0]
if _EXAMPLES not in sys.path:
    sys.path.insert(0, _EXAMPLES)

import display_driver  # noqa: E402 — wires LVGL display/input into the runtime
import lvgl as lv  # noqa: E402
from board_config import display_drv, runtime  # noqa: E402
from roku_engine import ROKU_HOST as _DEFAULT_HOST  # noqa: E402
from roku_engine import RokuEngine, ascii_label  # noqa: E402

# Override here, or leave "" and use SCAN / IP pad.
ROKU_HOST = _DEFAULT_HOST

# Toggle the animated "scanning" indicator on the Devices page.
_SHOW_SCAN_SPINNER = False

# Museum charcoal chassis + single violet accent.
_COL = {
    "bg_top": 0x0E1014,
    "bg_bot": 0x161A22,
    "plaque": 0x1A1F2A,
    "plaque_edge": 0x2A3140,
    "key": 0x323A4A,
    "key_alt": 0x272E3B,
    "accent": 0x7C5CFC,
    "accent2": 0x5A3ED0,
    "power": 0xE0574A,
    "power2": 0xB23A30,
    "transport": 0x3A5A72,
    "transport2": 0x274152,
    "ui": 0x232A36,
    "text": 0xF2F4F8,
    "muted": 0x9AA0B0,
    "on_accent": 0xFFFFFF,
    "dpad_ring": 0x1E2530,
}


def _hex(rgb):
    return lv.color_hex(rgb)


def _shade(rgb, factor):
    r = (rgb >> 16) & 0xFF
    g = (rgb >> 8) & 0xFF
    b = rgb & 0xFF
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return (r << 16) | (g << 8) | b


def _sym(name, fallback):
    sym = getattr(lv, "SYMBOL", None)
    if sym is not None:
        val = getattr(sym, name, None)
        if val:
            return val
    return fallback


def _pick_font(unit, ref_obj=None):
    if unit >= 560:
        candidates = (28, 24, 22, 20, 18, 16, 14, 12)
    elif unit >= 400:
        candidates = (22, 20, 18, 16, 14, 12)
    else:
        candidates = (16, 14, 12)
    for size in candidates:
        font = getattr(lv, "font_montserrat_" + str(size), None)
        if font is not None:
            return font
    if ref_obj is not None:
        for getter in ("theme_get_font_large", "theme_get_font_normal", "theme_get_font_small"):
            fn = getattr(lv, getter, None)
            if fn is None:
                continue
            try:
                font = fn(ref_obj)
                if font is not None:
                    return font
            except Exception:
                pass
    fn = getattr(lv, "font_get_default", None)
    if fn is not None:
        try:
            return fn()
        except Exception:
            pass
    return None


def _apply_font(obj, font):
    if font is not None:
        obj.set_style_text_font(font, 0)


def _no_scroll(obj):
    if hasattr(obj, "remove_flag"):
        obj.remove_flag(lv.obj.FLAG.SCROLLABLE)
    elif hasattr(obj, "clear_flag"):
        obj.clear_flag(lv.obj.FLAG.SCROLLABLE)


class _RokuLvgl:
    def __init__(self):
        self.engine = RokuEngine(host=ROKU_HOST)
        self.ip_buf = self.engine.host or ""
        self.page = "devices"
        self.app_offset = 0
        self.app_page_size = 1
        self.discover_list = []

        # Persistent (screen / plaque) styles vs per-page styles.
        self._styles = []
        self._page_styles = []

        # Cross-thread mailboxes: worker writes, lv.timer applies on main thread.
        self._pending_status = None
        self._pending_devices = []
        self._pending_rebuild = False
        self._playback_busy = False
        self._status_ticks = 0
        self._scan_busy = False
        self._last_scan_busy = False

        self.W = display_drv.width
        self.H = display_drv.height
        self.unit = min(self.W, self.H)
        self.pad = max(6, self.unit // 64)
        self.radius = max(8, self.unit // 26)
        self.plaque_h = max(64, self.H // 8)
        self.font = None
        self.font_sm = None
        self.name_lbl = None
        self.status_lbl = None
        self.content = None

        self.build_ui()

    # ----- styles ---------------------------------------------------------

    def _mk_style(self, page_scoped=True):
        style = lv.style_t()
        style.init()
        (self._page_styles if page_scoped else self._styles).append(style)
        return style

    def _panel_style(self, top, bottom, radius, edge=None, page_scoped=True):
        style = self._mk_style(page_scoped)
        style.set_bg_color(_hex(top))
        style.set_bg_opa(lv.OPA.COVER)
        if hasattr(style, "set_bg_grad_color") and bottom is not None and bottom != top:
            style.set_bg_grad_color(_hex(bottom))
            if hasattr(style, "set_bg_grad_dir"):
                style.set_bg_grad_dir(lv.GRAD_DIR.VER)
        style.set_radius(radius)
        if edge is not None:
            style.set_border_color(_hex(edge))
            style.set_border_width(1)
            style.set_border_opa(lv.OPA.COVER)
        else:
            style.set_border_width(0)
        return style

    # ----- build ----------------------------------------------------------

    def build_ui(self):
        inst = display_driver.event_loop.current_instance()
        if inst is not None:
            inst.disable()
        try:
            scr = lv.screen_active()
            self.font = _pick_font(self.unit, scr)
            self.font_sm = _pick_font(max(200, self.unit // 2), scr)

            bg = self._panel_style(
                _COL["bg_top"], _COL["bg_bot"], 0, page_scoped=False
            )
            scr.add_style(bg, 0)
            _no_scroll(scr)

            # Status plaque (persists across page swaps; only its text updates).
            plaque = lv.obj(scr)
            plaque.set_size(self.W - 2 * self.pad, self.plaque_h)
            plaque.align(lv.ALIGN.TOP_MID, 0, self.pad)
            plaque.add_style(
                self._panel_style(
                    _shade(_COL["plaque"], 1.15),
                    _COL["plaque"],
                    self.radius,
                    edge=_COL["plaque_edge"],
                    page_scoped=False,
                ),
                0,
            )
            _no_scroll(plaque)

            self.name_lbl = lv.label(plaque)
            self.name_lbl.set_text("Roku Remote")
            self.name_lbl.set_style_text_color(_hex(_COL["text"]), 0)
            _apply_font(self.name_lbl, self.font)
            self.name_lbl.align(lv.ALIGN.TOP_LEFT, self.pad, self.pad // 2)

            self.status_lbl = lv.label(plaque)
            self.status_lbl.set_text("Scanning...")
            self.status_lbl.set_style_text_color(_hex(_COL["muted"]), 0)
            _apply_font(self.status_lbl, self.font_sm)
            self.status_lbl.set_width(self.W - 4 * self.pad)
            self.status_lbl.align(lv.ALIGN.BOTTOM_LEFT, self.pad, -self.pad // 2)
            if hasattr(self.status_lbl, "set_long_mode"):
                lm = getattr(lv.label, "LONG_MODE", None)
                mode = None
                for name in ("DOT", "WRAP", "CLIP"):
                    mode = getattr(lm, name, None) if lm is not None else None
                    if mode is not None:
                        break
                if mode is not None:
                    self.status_lbl.set_long_mode(mode)

            # Content region below the plaque; cleaned + rebuilt per page.
            self.content = lv.obj(scr)
            self.content.set_size(self.W, self.H - self.plaque_h - 2 * self.pad)
            self.content.set_pos(0, self.plaque_h + 2 * self.pad)
            transparent = self._mk_style(page_scoped=False)
            transparent.set_bg_opa(lv.OPA.TRANSP)
            transparent.set_border_width(0)
            transparent.set_pad_all(0)
            self.content.add_style(transparent, 0)
            _no_scroll(self.content)

            self._show_page("devices")
        finally:
            if inst is not None:
                inst.enable()

        self._install_pump()
        self._start_scan()

    def _install_pump(self):
        self._timer = None
        creator = getattr(lv, "timer_create", None)
        if creator is not None:
            try:
                self._timer = creator(self._pump, 250, None)
            except Exception:
                self._timer = None

    # ----- button factory -------------------------------------------------

    def _role_colors(self, role):
        if role == "accent":
            return _COL["accent"], _COL["accent2"], _COL["on_accent"]
        if role == "power":
            return _COL["power"], _COL["power2"], _COL["text"]
        if role == "transport":
            return _COL["transport"], _COL["transport2"], _COL["text"]
        if role == "alt":
            return _COL["key_alt"], _shade(_COL["key_alt"], 0.7), _COL["text"]
        if role == "ui":
            return _COL["ui"], _shade(_COL["ui"], 0.7), _COL["muted"]
        return _COL["key"], _shade(_COL["key"], 0.7), _COL["text"]

    def _key_button(self, parent, text, x, y, w, h, role, on_click, round_btn=False, font=None):
        top, bottom, fg = self._role_colors(role)
        btn = lv.button(parent)
        btn.set_size(int(w), int(h))
        btn.set_pos(int(x), int(y))
        rad = (min(int(w), int(h)) // 2) if round_btn else self.radius

        style = self._panel_style(top, bottom, rad, edge=_shade(top, 0.55))
        if hasattr(style, "set_shadow_width"):
            style.set_shadow_width(max(4, self.pad))
            style.set_shadow_color(_hex(0x000000))
            if hasattr(style, "set_shadow_opa"):
                style.set_shadow_opa(lv.OPA._40)
            if hasattr(style, "set_shadow_ofs_y"):
                style.set_shadow_ofs_y(max(2, self.pad // 2))
        btn.add_style(style, 0)

        pressed = self._mk_style()
        pressed.set_bg_color(_hex(_shade(top, 1.25)))
        pressed.set_bg_opa(lv.OPA.COVER)
        if hasattr(pressed, "set_translate_y"):
            pressed.set_translate_y(max(1, self.pad // 3))
        btn.add_style(pressed, lv.STATE.PRESSED)

        lbl = lv.label(btn)
        lbl.set_text(text)
        lbl.set_style_text_color(_hex(fg), 0)
        _apply_font(lbl, font or self.font_sm)
        lbl.center()

        def _cb(e, _fn=on_click, _label=text):
            _fn()

        btn.add_event_cb(_cb, lv.EVENT.CLICKED, None)
        return btn

    # ----- pages ----------------------------------------------------------

    def _show_page(self, page):
        self.page = page
        if self.content is None:
            return
        self.content.clean()
        # Objects are deleted; drop their now-unreferenced styles.
        self._page_styles = []
        if page == "devices":
            self._build_devices()
        elif page == "apps":
            self._build_apps()
        elif page == "more":
            self._build_more()
        elif page == "ip":
            self._build_ip()
        else:
            self._build_remote()

    def _content_metrics(self):
        W = self.W
        H = self.content.get_height() if hasattr(self.content, "get_height") else (
            self.H - self.plaque_h - 2 * self.pad
        )
        return W, H

    def _row(self, w, row_h, row_bg):
        """Full-width transparent band; buttons align within it."""
        r = lv.obj(self.content)
        r.set_size(w, row_h)
        r.add_style(row_bg, 0)
        _no_scroll(r)
        return r

    def _place3(self, row, w, row_h, gap, specs):
        """Place up to three equal buttons: left / center / right of the band."""
        bw = (w - 2 * gap) // 3
        for (text, role, cb), al in zip(
            specs, (lv.ALIGN.LEFT_MID, lv.ALIGN.CENTER, lv.ALIGN.RIGHT_MID)
        ):
            btn = self._key_button(row, text, 0, 0, bw, row_h, role, cb)
            btn.align(al, 0, 0)

    def _build_remote(self):
        W, H = self._content_metrics()
        pad = self.pad
        gap = pad
        w = W - 2 * pad

        # One shared transparent style for every row band on this page.
        row_bg = self._mk_style()
        row_bg.set_bg_opa(lv.OPA.TRANSP)
        row_bg.set_border_width(0)
        row_bg.set_pad_all(0)

        # A prominent D-pad plus six equal button rows, sized to the content.
        ring = max(150, int(min(w * 0.6, H * 0.34)))
        row_h = max(38, (H - ring - 7 * gap) // 6)

        # 1) Utility row anchored to the top; rows below stack via align_to.
        util = self._row(w, row_h, row_bg)
        util.align(lv.ALIGN.TOP_MID, 0, 0)
        self._place3(util, w, row_h, gap, [
            (_sym("LEFT", "BACK"), "key", lambda: self._ecp("Back")),
            (_sym("HOME", "HOME"), "accent", lambda: self._ecp("Home")),
            (_sym("POWER", "PWR") + " " + self.engine.power_label(), "power", self._toggle_power),
        ])

        # 2) Circular D-pad ring, centered under the utility row.
        ringobj = lv.obj(self.content)
        ringobj.set_size(ring, ring)
        ringobj.add_style(
            self._panel_style(_COL["dpad_ring"], _shade(_COL["dpad_ring"], 0.7),
                              ring // 2, edge=_COL["plaque_edge"]),
            0,
        )
        _no_scroll(ringobj)
        ringobj.align_to(util, lv.ALIGN.OUT_BOTTOM_MID, 0, gap)

        cell = ring // 3
        inset = max(4, cell // 6)
        arrow = cell - 2 * inset
        oksz = cell - 4
        # OK centered on the ring; arrows centered on each axis.
        up = self._key_button(ringobj, _sym("UP", "^"), 0, 0, arrow, arrow, "key",
                              lambda: self._ecp("Up"), round_btn=True)
        up.align(lv.ALIGN.TOP_MID, 0, inset)
        down = self._key_button(ringobj, _sym("DOWN", "v"), 0, 0, arrow, arrow, "key",
                                lambda: self._ecp("Down"), round_btn=True)
        down.align(lv.ALIGN.BOTTOM_MID, 0, -inset)
        left = self._key_button(ringobj, _sym("LEFT", "<"), 0, 0, arrow, arrow, "key",
                                lambda: self._ecp("Left"), round_btn=True)
        left.align(lv.ALIGN.LEFT_MID, inset, 0)
        right = self._key_button(ringobj, _sym("RIGHT", ">"), 0, 0, arrow, arrow, "key",
                                 lambda: self._ecp("Right"), round_btn=True)
        right.align(lv.ALIGN.RIGHT_MID, -inset, 0)
        ok = self._key_button(ringobj, "OK", 0, 0, oksz, oksz, "accent",
                              lambda: self._ecp("Select"), round_btn=True, font=self.font)
        ok.align(lv.ALIGN.CENTER, 0, 0)

        # 3) Options row: Replay | Options | Search.
        opts = self._row(w, row_h, row_bg)
        opts.align_to(ringobj, lv.ALIGN.OUT_BOTTOM_MID, 0, gap)
        self._place3(opts, w, row_h, gap, [
            (_sym("REFRESH", "RPL"), "alt", lambda: self._ecp("InstantReplay")),
            (_sym("LIST", "*"), "alt", lambda: self._ecp("Info")),
            (_sym("AUDIO", "SRCH"), "alt", lambda: self._ecp("Search")),
        ])

        # 4) Transport row: Rewind | Play/Pause | Forward.
        play = _sym("PAUSE", "||") if self.engine.play_label() == "PAUSE" else _sym("PLAY", ">")
        trans = self._row(w, row_h, row_bg)
        trans.align_to(opts, lv.ALIGN.OUT_BOTTOM_MID, 0, gap)
        self._place3(trans, w, row_h, gap, [
            (_sym("PREV", "<<"), "transport", lambda: self._ecp("Rev")),
            (play, "transport", lambda: self._ecp("Play")),
            (_sym("NEXT", ">>"), "transport", lambda: self._ecp("Fwd")),
        ])

        # 5) Volume row (relocated from the sides into the open bottom area).
        vol = self._row(w, row_h, row_bg)
        vol.align_to(trans, lv.ALIGN.OUT_BOTTOM_MID, 0, gap)
        self._place3(vol, w, row_h, gap, [
            (_sym("VOLUME_MID", "VOL-"), "key", lambda: self._ecp("VolumeDown")),
            (_sym("MUTE", "MUTE"), "alt", lambda: self._ecp("VolumeMute")),
            (_sym("VOLUME_MAX", "VOL+"), "key", lambda: self._ecp("VolumeUp")),
        ])

        # 6) Channel row.
        chan = self._row(w, row_h, row_bg)
        chan.align_to(vol, lv.ALIGN.OUT_BOTTOM_MID, 0, gap)
        self._place3(chan, w, row_h, gap, [
            ("CH-", "key", lambda: self._ecp("ChannelDown")),
            (_sym("OK", "ENT"), "alt", lambda: self._ecp("Enter")),
            ("CH+", "key", lambda: self._ecp("ChannelUp")),
        ])

        # 7) Chrome row: APPS | MORE | SCAN.
        chrome = self._row(w, row_h, row_bg)
        chrome.align_to(chan, lv.ALIGN.OUT_BOTTOM_MID, 0, gap)
        self._place3(chrome, w, row_h, gap, [
            ("APPS", "ui", self._open_apps),
            ("MORE", "ui", lambda: self._show_page("more")),
            ("SCAN", "ui", self._rescan),
        ])

    def _build_devices(self):
        W, H = self._content_metrics()
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(40, H // 11)
        self._key_button(self.content, "REMOTE", x0, 0, (w - gap) // 2, row_h, "ui",
                         lambda: self._show_page("remote"))
        self._key_button(self.content, "RESCAN", x0 + (w - gap) // 2 + gap, 0,
                         (w - gap) // 2, row_h, "accent", self._rescan)
        y = row_h + gap
        slot_h = max(44, self.plaque_h - 2 * pad)
        devices = self.discover_list or []
        avail = H - y
        max_slots = max(1, (avail + gap) // (slot_h + gap))
        for i, dev in enumerate(devices[:max_slots]):
            label = ascii_label((dev.get("name") or "").strip() or "Roku")
            self._key_button(
                self.content, label, x0, y + i * (slot_h + gap), w, slot_h,
                "accent" if i == 0 else "key", (lambda d=dev: self._pick_device(d)),
                font=self.font,
            )
        if self._scan_busy and _SHOW_SCAN_SPINNER:
            self._build_scan_indicator(x0, w, y + len(devices[:max_slots]) * (slot_h + gap), H)

    def _build_scan_indicator(self, x0, w, y, H):
        """Animated 'working' clue so the user knows discovery is not hung."""
        spin = max(28, min(w // 4, (H - y) - self.pad))
        if spin < 24:
            return
        cx = x0 + (w - spin) // 2
        made = False
        if hasattr(lv, "spinner"):
            try:
                sp = lv.spinner(self.content)
                sp.set_size(spin, spin)
                made = True
            except (TypeError, AttributeError):
                try:
                    sp = lv.spinner(self.content, 1000, 60)
                    sp.set_size(spin, spin)
                    made = True
                except Exception:
                    made = False
            if made:
                try:
                    _no_scroll(sp)
                    sp.set_pos(cx, y)
                    sp.set_style_arc_color(_hex(_COL["accent"]), lv.PART.INDICATOR)
                    sp.set_style_arc_color(_hex(_COL["plaque_edge"]), lv.PART.MAIN)
                except Exception:
                    pass
        if not made:
            # Fallback: a pulsing accent dot driven by the LVGL animation timer.
            dot = lv.obj(self.content)
            dsz = max(16, spin // 2)
            dot.set_size(dsz, dsz)
            dot.add_style(
                self._panel_style(_COL["accent"], _shade(_COL["accent"], 0.7), dsz // 2),
                0,
            )
            _no_scroll(dot)
            dot.set_pos(x0 + (w - dsz) // 2, y)
            try:
                a = lv.anim_t()
                a.init()
                a.set_var(dot)
                a.set_values(lv.OPA.COVER, lv.OPA._40)
                a.set_time(500)
                a.set_playback_time(500)
                a.set_repeat_count(lv.ANIM_REPEAT.INFINITE)
                a.set_custom_exec_cb(lambda _a, v: dot.set_style_opa(v, 0))
                lv.anim_t.start(a)
            except Exception:
                pass

    def _build_apps(self):
        W, H = self._content_metrics()
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(40, H // 11)
        third = (w - 2 * gap) // 3
        self._key_button(self.content, "REMOTE", x0, 0, third, row_h, "ui",
                         lambda: self._show_page("remote"))
        self._key_button(self.content, "REFRESH", x0 + third + gap, 0, third, row_h, "ui",
                         self._refresh_apps)
        self._key_button(self.content, "NEXT", x0 + 2 * (third + gap), 0, third, row_h, "ui",
                         self._apps_next)
        y = row_h + gap
        cols = 3
        bw = (w - gap * (cols - 1)) // cols
        bh = bw
        avail = H - y
        rows = max(1, (avail + gap) // (bh + gap))
        max_slots = rows * cols
        self.app_page_size = max_slots
        apps = self.engine.apps or []
        window = apps[self.app_offset : self.app_offset + max_slots]
        for i, app in enumerate(window):
            name = ascii_label(app.get("name") or app.get("id") or "?")
            col = i % cols
            row = i // cols
            self._key_button(
                self.content, name, x0 + col * (bw + gap), y + row * (bh + gap), bw, bh,
                "accent" if i == 0 else "key", (lambda a=app: self._launch(a)),
            )

    def _build_more(self):
        W, H = self._content_metrics()
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(40, H // 11)
        half = (w - gap) // 2
        self._key_button(self.content, "REMOTE", x0, 0, half, row_h, "ui",
                         lambda: self._show_page("remote"))
        self._key_button(self.content, "IP", x0 + half + gap, 0, half, row_h, "ui",
                         lambda: self._show_page("ip"))
        y = row_h + gap
        actions = (
            ("DEVICE INFO", self._show_dev_info),
            ("MEDIA", self._show_media),
            ("TV CHANNEL", self._show_tv_channel),
            ("PERF", self._show_perf),
        )
        for i, (lab, fn) in enumerate(actions):
            col = i % 2
            row = i // 2
            self._key_button(self.content, lab, x0 + col * (half + gap),
                             y + row * (row_h + gap), half, row_h, "key", fn)

    def _build_ip(self):
        W, H = self._content_metrics()
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(40, H // 11)
        third = (w - 2 * gap) // 3
        self._key_button(self.content, "BACK", x0, 0, third, row_h, "ui",
                         lambda: self._show_page("more"))
        self._key_button(self.content, "CLR", x0 + third + gap, 0, third, row_h, "ui",
                         self._ip_clear)
        self._key_button(self.content, "SET", x0 + 2 * (third + gap), 0, third, row_h, "accent",
                         self._ip_set)
        y = row_h + gap
        shown = self.ip_buf if self.ip_buf else "(empty)"
        self._key_button(self.content, shown, x0, y, w, row_h, "alt", lambda: None, font=self.font)
        y += row_h + gap
        keys = "123456789.0<"
        cols = 3
        bw = (w - gap * (cols - 1)) // cols
        for i, ch in enumerate(keys):
            col = i % cols
            row = i // cols
            lab = _sym("BACKSPACE", "BS") if ch == "<" else ch
            self._key_button(self.content, lab, x0 + col * (bw + gap), y + row * (row_h + gap),
                             bw, row_h, "key", (lambda c=ch: self._ip_key(c)))

    # ----- navigation -----------------------------------------------------

    def _open_apps(self):
        self.app_offset = 0
        if self.engine.apps:
            self._set_status("%d apps" % len(self.engine.apps))
            self._show_page("apps")
        else:
            self._refresh_apps()

    def _apps_next(self):
        n = len(self.engine.apps or [])
        step = max(1, int(self.app_page_size or 1))
        if n:
            self.app_offset = (self.app_offset + step) % n
        self._show_page("apps")

    # ----- status ---------------------------------------------------------

    def _set_status(self, line):
        if self.status_lbl is not None:
            self.status_lbl.set_text(ascii_label(line if line is not None else ""))

    def _set_name(self, line):
        if self.name_lbl is not None:
            self.name_lbl.set_text(ascii_label(line or "Roku Remote"))

    def _queue_status(self, line):
        if line is not None:
            self._pending_status = ascii_label(line)

    # ----- ECP actions (worker thread; no LVGL calls) ---------------------

    def _run_bg(self, fn):
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

    def _ecp(self, key):
        self._set_status(key)

        def _work():
            self.engine.press(key)
            self._queue_status(self.engine.refresh_playback())

        self._run_bg(_work)

    def _toggle_power(self):
        key = self.engine.mark_power_optimistic()
        self._set_status(key)
        if self.page == "remote":
            self._show_page("remote")

        def _work():
            self.engine.press(key)
            try:
                self.engine.query_device_info()
                self._queue_status(self.engine.refresh_playback())
            except Exception:
                pass

        self._run_bg(_work)

    def _launch(self, app):
        app_id = app.get("id", "")
        self._set_status("launch " + ascii_label(app.get("name") or ""))

        def _work():
            self.engine.launch_refresh(app_id)
            self._queue_status(self.engine.playback_status())

        self._run_bg(_work)

    def _refresh_apps(self):
        self.app_offset = 0
        self._set_status("loading apps...")
        self._show_page("apps")

        def _work():
            self.engine.query_apps()
            n = len(self.engine.apps or [])
            self._queue_status(("%d apps" % n) if n else (self.engine.last_error or "no apps"))
            self._pending_rebuild = True

        self._run_bg(_work)

    def _show_dev_info(self):
        self._set_status("device info...")

        def _work():
            info = self.engine.query_device_info()
            line = (info.get("model-name", "") + " " + info.get("power-mode", "")).strip()
            self._queue_status(line or self.engine.last_error or "no info")

        self._run_bg(_work)

    def _show_media(self):
        self._set_status("media...")

        def _work():
            self._queue_status(self.engine.refresh_playback() or "no media")

        self._run_bg(_work)

    def _show_tv_channel(self):
        self._set_status("tv channel...")

        def _work():
            raw = self.engine.query_tv_active_channel() or self.engine.query_tv_channels()
            self._queue_status((raw.replace("\n", " ")[:48]) if raw else "n/a")

        self._run_bg(_work)

    def _show_perf(self):
        self._set_status("perf...")

        def _work():
            raw = self.engine.query_chanperf()
            self._queue_status(
                (raw.replace("\n", " ")[:48]) if raw else (self.engine.last_error or "perf n/a")
            )

        self._run_bg(_work)

    # ----- IP entry -------------------------------------------------------

    def _ip_clear(self):
        self.ip_buf = ""
        self._show_page("ip")

    def _ip_key(self, ch):
        if ch == "<":
            self.ip_buf = self.ip_buf[:-1]
        elif len(self.ip_buf) < 15:
            self.ip_buf += ch
        self._show_page("ip")

    def _ip_set(self):
        self.engine.set_host(self.ip_buf)
        self.app_offset = 0
        self._set_name(self.ip_buf or "Roku")
        self._set_status("connecting " + (self.ip_buf or "?"))
        self._show_page("remote")

        def _work():
            self.engine.connect(discover_if_empty=False)
            self._queue_status(self.engine.playback_status())
            self._pending_rebuild = True

        self._run_bg(_work)

    # ----- discovery ------------------------------------------------------

    def _pick_device(self, dev):
        host = (dev or {}).get("host") or ""
        name = ((dev or {}).get("name") or "").strip() or host
        if not host:
            self._set_status("no host")
            return
        self.engine.set_host(host)
        self.ip_buf = host
        self.app_offset = 0
        self._set_name(name)
        self._set_status(name)
        self._show_page("remote")

        def _work():
            self.engine.connect(discover_if_empty=False)
            self._queue_status(self.engine.playback_status())
            self._pending_rebuild = True

        self._run_bg(_work)

    def _rescan(self):
        self.discover_list = []
        self._pending_devices = []
        self._set_status("Scanning...")
        self._start_scan()

    def _start_scan(self):
        if self._scan_busy:
            return
        self._scan_busy = True
        self._last_scan_busy = True
        # Rebuild the devices page now that scanning is active so the animated
        # working indicator is visible immediately (not only after a device).
        self._show_page("devices")

        def _on_device(dev):
            host = (dev or {}).get("host") or ""
            if not host:
                return
            for d in self._pending_devices:
                if d.get("host") == host:
                    return
            self._pending_devices.append(dev)

        def _work():
            try:
                devices = self.engine.discover(
                    timeout=8.0, retries=1, ssdp=True, scan_fallback=True, on_device=_on_device
                )
                for dev in devices or []:
                    _on_device(dev)
                if not (devices or self._pending_devices):
                    self._queue_status(self.engine.last_error or "no Roku found")
                else:
                    self._queue_status("found %d - pick one" % len(self._pending_devices))
            except Exception as e:
                self._queue_status(str(e))
            finally:
                self._scan_busy = False

        self._run_bg(_work)

    # ----- soft pump (LVGL main thread) -----------------------------------

    def _pump(self, _timer=None):
        if self._pending_status is not None:
            self._set_status(self._pending_status)
            self._pending_status = None

        if self._pending_devices and self.page == "devices":
            known = {d.get("host") for d in self.discover_list}
            new = [d for d in self._pending_devices if d.get("host") not in known]
            if new:
                self.discover_list.extend(new)
                self._show_page("devices")

        if self._last_scan_busy and not self._scan_busy:
            self._last_scan_busy = False
            if self.page == "devices":
                self._show_page("devices")

        if self._pending_rebuild:
            self._pending_rebuild = False
            if self.page == "remote":
                self._show_page("remote")

        self._status_ticks += 1
        if (
            self.page == "remote"
            and self.engine.connected
            and self._status_ticks % 40 == 0
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


_remote = _RokuLvgl()

# Canonical entry: display_driver wired LVGL into the shared runtime at import;
# run_forever() keeps the app alive (or returns immediately in a signal-driven
# interactive REPL).
runtime.run_forever()
