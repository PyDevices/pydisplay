# deps: pdwidgets
# modules: roku_engine
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
roku_widgets
====================================================
Portrait Roku remote built with ``pdwidgets``.

One of three interchangeable Roku front ends (``roku_graphics``,
``roku_widgets``, ``roku_lvgl``) that all drive the same
:class:`roku_engine.RokuEngine`. Layout, padding, and text scales are derived
from ``display.width`` / ``height`` so the UI scales from 320x480 up through
tall phone portraits.

Input and frame rendering are driven by the shared ``eventsys.Runtime``:
``pd.Display`` wires them in at construction, so the example just builds the UI
and hands control to ``runtime.run_forever()``. Blocking ECP calls run on a
worker thread; widget mutations are applied from a soft ``multimer.Timer`` pump
on the main tick so the render loop never races the worker.

Launch via ``roku_remote`` (prefs + MRU). Direct ``roku_widgets.run()`` also works.
Requires Roku **Control by mobile apps -> Enabled**. Join WiFi before running
on a microcontroller.
"""

import sys
import time

_EXAMPLES = __file__.replace("\\", "/").rsplit("/", 1)[0]
if _EXAMPLES not in sys.path:
    sys.path.insert(0, _EXAMPLES)

import board_config
import pdwidgets as pd
from eventsys.keys import Keys
from multimer import Timer
from roku_engine import (
    FRONTEND_BUTTONS,
    RokuEngine,
    ascii_label,
    format_delete_status_chars,
    format_switch_status,
    other_frontends,
    set_frontend,
)

pd.DEBUG = False

FRONTEND = "widgets"

_KEY_MAP = {
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


class _RemoteUI:
    """pdwidgets front end. Pages are rebuilt in-place under one content panel."""

    def __init__(self, engine=None, start_page="devices"):
        self.display = pd.Display(board_config.display_drv, board_config.runtime)
        self.runtime = board_config.runtime
        pal = self.display.pal
        self.W = self.display.width
        self.H = self.display.height
        self.unit = min(self.W, self.H)

        self.pad = max(3, self.unit // 64)
        self.radius = max(4, self.unit // 40)
        self.status_h = max(28, self.unit // 12)
        self.btn_text = 16 if self.unit >= 400 else 14
        if self.btn_text not in (8, 14, 16):
            self.btn_text = 16

        # Dark remote palette (mirrors the graphics "midnight" chassis).
        self.BG = pal.color565(0x12, 0x14, 0x1A)
        self.STATUS_BG = pal.color565(0x1C, 0x22, 0x2E)
        self.KEY_BG = pal.color565(0x3A, 0x40, 0x4E)
        self.ALT_BG = pal.color565(0x2E, 0x34, 0x40)
        self.ACCENT_BG = pal.color565(0x7C, 0x5C, 0xFC)
        self.POWER_BG = pal.color565(0xE0, 0x5A, 0x4A)
        self.TRANSPORT_BG = pal.color565(0x3A, 0x5A, 0x72)
        self.UI_BG = pal.color565(0x24, 0x28, 0x34)
        self.TEXT = pal.color565(0xF2, 0xF4, 0xF8)
        self.MUTED = pal.color565(0x9A, 0xA0, 0xB0)
        self.ON_ACCENT = pal.color565(0xFF, 0xFF, 0xFF)

        self.engine = engine if engine is not None else RokuEngine()
        self.ip_buf = self.engine.host or ""
        self.page = (
            start_page if start_page in ("devices", "remote", "apps", "more") else "devices"
        )
        self.app_offset = 0
        self.app_page_size = 1
        self.selected_app_id = ""
        self.discover_list = []
        self._delete_armed = None
        self._switch_armed = None

        # Cross-thread mailboxes (worker writes, soft pump applies on main tick).
        self._pending_status = None
        self._pending_devices = []
        self._pending_select_list = None
        self._pending_rebuild = False
        self._chrome_face = ""
        self._pending_chrome = False
        self._play_btn = None
        self._power_btn = None
        self._playback_busy = False
        self._status_ticks = 0
        self._scan_busy = False
        self._pending_scan = False
        self._scan_yield = False
        self._press_t0 = 0
        self._press_dev = None

        self.screen = pd.Screen(self.display, bg=self.BG, visible=False)
        self.status = pd.Label(
            self.screen,
            value="Scanning...",
            align=pd.ALIGN.TOP_LEFT,
            x=self.pad,
            y=max(2, (self.status_h - self.btn_text) // 2),
            fg=self.MUTED,
            text_height=self.btn_text,
        )
        # Content panel below the status band; children rebuilt per page.
        self.content = pd.Widget(
            self.screen,
            w=self.W,
            h=self.H - self.status_h,
            align=pd.ALIGN.BOTTOM,
            bg=self.BG,
            padding=(0, 0, 0, 0),
        )

        self.screen.add_event_cb(pd.events.KEYDOWN, self._on_key)

        self._build_page()
        self.screen.visible = True

        # Soft pump: apply worker results + periodic playback refresh on main tick.
        self._pump_timer = Timer(-1)
        try:
            self._pump_timer.init(
                mode=Timer.PERIODIC, period=250, callback=self._pump, hard=False
            )
        except Exception:
            pass

        if self.page == "remote" and (self.engine.host or "").strip():
            self._set_status(self.engine.playback_status() or "ready")
            self._refresh_playback_bg()
        else:
            self._open_select(soft_refresh=True)

    # ----- helpers --------------------------------------------------------

    def _run_bg(self, fn):
        """Run ``fn`` off the input/render path; inline fallback when no threads."""
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

    def _queue_status(self, line):
        if line is None:
            return
        self._pending_status = ascii_label(line)

    def _set_status(self, line):
        self.status.value = ascii_label(line if line is not None else "")

    def _clear_content(self):
        for child in list(self.content.children):
            self.content.remove_child(child)

    def _colors_for(self, role):
        if role == "accent":
            return self.ON_ACCENT, self.ACCENT_BG
        if role == "power":
            return self.TEXT, self.POWER_BG
        if role == "transport":
            return self.TEXT, self.TRANSPORT_BG
        if role == "alt":
            return self.TEXT, self.ALT_BG
        if role == "ui":
            return self.MUTED, self.UI_BG
        return self.TEXT, self.KEY_BG

    def _button(self, label, x, y, w, h, on_click, role="key"):
        fg, bg = self._colors_for(role)
        btn = pd.Button(
            self.content,
            label=label,
            x=int(x),
            y=int(y),
            w=int(w),
            h=int(h),
            radius=self.radius,
            fg=bg,
            bg=bg,
            text_color=fg,
            text_height=self.btn_text,
            shadow=0,
        )

        def _cb(sender, event, _fn=on_click):
            _fn()

        btn.add_event_cb(pd.events.MOUSEBUTTONUP, _cb)
        return btn

    def _device_button(self, label, x, y, w, h, dev, role="key"):
        """Select-page TV row: short tap picks, long-press arms delete."""
        fg, bg = self._colors_for(role)
        btn = pd.Button(
            self.content,
            label=label,
            x=int(x),
            y=int(y),
            w=int(w),
            h=int(h),
            radius=self.radius,
            fg=bg,
            bg=bg,
            text_color=fg,
            text_height=self.btn_text,
            shadow=0,
        )

        def _now_ms():
            try:
                if hasattr(time, "ticks_ms"):
                    return time.ticks_ms()
            except Exception:
                pass
            return int(time.time() * 1000)

        def _down(_sender, _event, d=dev):
            self._press_t0 = _now_ms()
            self._press_dev = d

        def _up(_sender, _event, d=dev):
            t0 = self._press_t0
            self._press_t0 = 0
            if self._press_dev is not d:
                return
            dt = _now_ms() - t0
            try:
                if hasattr(time, "ticks_diff") and hasattr(time, "ticks_ms"):
                    dt = time.ticks_diff(_now_ms(), t0)
            except Exception:
                pass
            if dt >= 550:
                self._arm_delete(d)
            else:
                self._pick_device(d)

        down_ev = getattr(pd.events, "MOUSEBUTTONDOWN", None)
        if down_ev is not None:
            btn.add_event_cb(down_ev, _down)
        btn.add_event_cb(pd.events.MOUSEBUTTONUP, _up)
        return btn

    # ----- page building --------------------------------------------------

    def _build_page(self):
        self._play_btn = None
        self._power_btn = None
        self._clear_content()
        if self.page == "devices":
            self._build_devices()
        elif self.page == "apps":
            self._build_apps()
        elif self.page == "more":
            self._build_more()
        else:
            self._build_remote()

    def _build_remote(self):
        W = self.content.width
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(34, self.content.height // 12)
        y = pad

        # Utility row: BACK | HOME | PWR
        bw = (w - 2 * gap) // 3
        self._button("BACK", x0, y, bw, row_h, lambda: self._ecp("Back"), "key")
        self._button("HOME", x0 + bw + gap, y, bw, row_h, lambda: self._ecp("Home"), "accent")
        self._power_btn = self._button(
            "PWR " + self.engine.power_label(),
            x0 + 2 * (bw + gap),
            y,
            bw,
            row_h,
            self._toggle_power,
            "power",
        )
        y += row_h + gap * 2

        # D-pad 3x3
        dpad = min(w, max(150, self.content.height // 3))
        dx = x0 + (w - dpad) // 2
        cell = dpad // 3
        self._button("^", dx + cell, y, cell, cell, lambda: self._ecp("Up"), "key")
        self._button("<", dx, y + cell, cell, cell, lambda: self._ecp("Left"), "key")
        self._button("OK", dx + cell, y + cell, cell, cell, lambda: self._ecp("Select"), "accent")
        self._button(">", dx + 2 * cell, y + cell, cell, cell, lambda: self._ecp("Right"), "key")
        self._button("v", dx + cell, y + 2 * cell, cell, cell, lambda: self._ecp("Down"), "key")
        y += dpad + gap * 2

        # Mid row: REPLAY | * | CC (closed captions)
        bw = (w - 2 * gap) // 3
        self._button("REPLAY", x0, y, bw, row_h, lambda: self._ecp("InstantReplay"), "key")
        self._button("*", x0 + bw + gap, y, bw, row_h, lambda: self._ecp("Info"), "key")
        self._button("CC", x0 + 2 * (bw + gap), y, bw, row_h, lambda: self._ecp("ClosedCaption"), "key")
        y += row_h + gap

        # Transport: << | PLAY | >>
        play_face = self.engine.play_label()
        self._chrome_face = "%s|%s" % (play_face, self.engine.power_label())
        self._button("<<", x0, y, bw, row_h, lambda: self._ecp("Rev"), "transport")
        self._play_btn = self._button(
            play_face,
            x0 + bw + gap,
            y,
            bw,
            row_h,
            lambda: self._ecp("Play"),
            "transport",
        )
        self._button(">>", x0 + 2 * (bw + gap), y, bw, row_h, lambda: self._ecp("Fwd"), "transport")
        y += row_h + gap

        # Volume: VOL- | MUTE | VOL+
        self._button("VOL-", x0, y, bw, row_h, lambda: self._ecp("VolumeDown"), "alt")
        self._button("MUTE", x0 + bw + gap, y, bw, row_h, lambda: self._ecp("VolumeMute"), "alt")
        self._button("VOL+", x0 + 2 * (bw + gap), y, bw, row_h, lambda: self._ecp("VolumeUp"), "alt")
        y += row_h + gap

        # Channel: CH- | ENT | CH+
        self._button("CH-", x0, y, bw, row_h, lambda: self._ecp("ChannelDown"), "key")
        self._button("ENT", x0 + bw + gap, y, bw, row_h, lambda: self._ecp("Enter"), "alt")
        self._button("CH+", x0 + 2 * (bw + gap), y, bw, row_h, lambda: self._ecp("ChannelUp"), "key")
        y += row_h + gap

        # Chrome: APPS | MORE | SELECT
        bh = max(30, row_h - 4)
        self._button("APPS", x0, y, bw, bh, self._open_apps, "ui")
        self._button("MORE", x0 + bw + gap, y, bw, bh, self._open_more, "ui")
        self._button("SELECT", x0 + 2 * (bw + gap), y, bw, bh, self._open_select, "ui")

    def _build_devices(self):
        W = self.content.width
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(34, self.content.height // 12)
        self._button("REMOTE", x0, pad, (w - gap) // 2, row_h, self._goto_remote, "ui")
        self._button(
            "SCAN",
            x0 + (w - gap) // 2 + gap,
            pad,
            (w - gap) // 2,
            row_h,
            self._scan_button,
            "accent",
        )
        y = pad + row_h + gap
        slot_h = max(34, self.status_h)
        devices = self.discover_list or []
        avail = self.content.height - y - pad
        max_slots = max(1, (avail + gap) // (slot_h + gap))
        for i, dev in enumerate(devices[:max_slots]):
            name = ascii_label((dev.get("name") or "").strip() or "")
            host = ascii_label((dev.get("host") or "").strip() or "")
            label = name or host or "Roku"
            self._device_button(
                label,
                x0,
                y + i * (slot_h + gap),
                w,
                slot_h,
                dev,
                "accent" if i == 0 else "key",
            )

    def _build_apps(self):
        W = self.content.width
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(34, self.content.height // 12)
        third = (w - 2 * gap) // 3
        self._button("REMOTE", x0, pad, third, row_h, self._goto_remote, "ui")
        self._button("REFRESH", x0 + third + gap, pad, third, row_h, self._refresh_apps, "ui")
        self._button("NEXT", x0 + 2 * (third + gap), pad, third, row_h, self._apps_next, "ui")
        y = pad + row_h + gap

        cols = 3
        bw = (w - gap * (cols - 1)) // cols
        bh = bw
        avail = self.content.height - y - pad
        rows = max(1, (avail + gap) // (bh + gap))
        max_slots = rows * cols
        self.app_page_size = max_slots
        apps = self.engine.store_apps()
        window = apps[self.app_offset : self.app_offset + max_slots]
        sel = str(
            self.selected_app_id
            or (self.engine.active_app or {}).get("id")
            or ""
        )
        for i, app in enumerate(window):
            name = ascii_label(app.get("name") or app.get("id") or "?")
            col = i % cols
            row = i // cols
            aid = str(app.get("id") or "")
            self._button(
                name,
                x0 + col * (bw + gap),
                y + row * (bh + gap),
                bw,
                bh,
                (lambda a=app: self._launch(a)),
                "accent" if aid and aid == sel else "key",
            )

    def _build_more(self):
        W = self.content.width
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(34, self.content.height // 12)
        half = (w - gap) // 2
        third = (w - 2 * gap) // 3
        others = other_frontends(FRONTEND)
        self._button("REMOTE", x0, pad, third, row_h, self._goto_remote, "ui")
        for i, fe in enumerate(others[:2]):
            lab = FRONTEND_BUTTONS.get(fe, fe.upper())
            self._button(
                lab,
                x0 + (i + 1) * (third + gap),
                pad,
                third,
                row_h,
                (lambda f=fe: self._arm_switch(f)),
                "ui",
            )
        y = pad + row_h + gap
        inputs = self.engine.inputs()
        if not inputs:
            self._button("no inputs", x0, y, w, row_h, lambda: None, "alt")
            return
        avail = self.content.height - y - pad
        max_slots = max(1, (avail + gap) // (row_h + gap)) * 2
        for i, app in enumerate(inputs[:max_slots]):
            lab = ascii_label((app.get("name") or "").strip())
            if not lab:
                lab = self.engine.input_short_label(app, max_chars=10)
            col = i % 2
            row = i // 2
            self._button(
                lab,
                x0 + col * (half + gap),
                y + row * (row_h + gap),
                half,
                row_h,
                (lambda a=app: self._launch(a)),
                "alt",
            )

    # ----- navigation -----------------------------------------------------

    def _goto(self, page):
        self.page = page
        self._build_page()
        if page == "remote":
            # Always re-probe — clears sticky apps/inputs plaque text and
            # recovers from a false "offline" after a transient error.
            self._refresh_playback_bg()

    def _arm_switch(self, frontend):
        self._switch_armed = frontend
        self._set_status(
            format_switch_status(
                frontend,
                fits=lambda s: len(s) <= self._status_max_chars(),
                tail=" press REMOTE",
            )
        )

    def _confirm_switch(self):
        fe = self._switch_armed
        self._switch_armed = None
        if not fe:
            return False
        try:
            ok = set_frontend(fe)
        except Exception:
            ok = False
        if not ok:
            self._set_status("save failed")
            return True
        self._set_status("restart app")
        return True

    def _goto_remote(self):
        if self._switch_armed:
            self._confirm_switch()
            return
        host = (self.engine.host or "").strip()
        if not host:
            self._set_status("pick a TV first")
            return
        self._goto("remote")

    def _open_more(self):
        self._switch_armed = None
        self._goto("more")
        if self.engine.apps:
            n = len(self.engine.inputs() or [])
            if n:
                self._set_status("%d inputs" % n)
            return
        self._set_status("loading inputs...")

        def _work():
            self.engine.query_apps()
            n = len(self.engine.inputs() or [])
            self._queue_status(("%d inputs" % n) if n else "no inputs")
            self._pending_rebuild = True

        self._run_bg(_work)

    def _open_apps(self):
        self.page = "apps"
        self.app_offset = 0
        if not self.selected_app_id:
            self.selected_app_id = str((self.engine.active_app or {}).get("id") or "")
        if self.engine.apps:
            self._set_status("%d apps" % len(self.engine.store_apps()))
            self._build_page()
        else:
            self._refresh_apps()

    def _apps_next(self):
        n = len(self.engine.store_apps())
        step = max(1, int(self.app_page_size or 1))
        if n:
            self.app_offset = (self.app_offset + step) % n
        self._build_page()

    # ----- ECP actions ----------------------------------------------------

    def _set_btn_label(self, btn, text):
        if btn is None:
            return
        lab = getattr(btn, "label", None)
        if lab is None:
            return
        try:
            lab.value = ascii_label(text)
        except Exception:
            pass

    def _apply_chrome_face(self):
        play_face = self.engine.play_label()
        power_face = self.engine.power_label()
        self._chrome_face = "%s|%s" % (play_face, power_face)
        self._set_btn_label(self._play_btn, play_face)
        self._set_btn_label(self._power_btn, "PWR " + power_face)

    def _note_playback_chrome(self, line=None, force_rebuild=False):
        """Mailbox plaque text; queue in-place play/power label update."""
        if line is not None:
            self._queue_status(line)
        aid = str((self.engine.active_app or {}).get("id") or "")
        if aid:
            self.selected_app_id = aid
        face = "%s|%s" % (self.engine.play_label(), self.engine.power_label())
        if self.page != "remote":
            self._chrome_face = face
            return
        if force_rebuild:
            self._chrome_face = face
            self._pending_rebuild = True
            return
        if face != self._chrome_face:
            self._chrome_face = face
            self._pending_chrome = True

    def _ecp(self, key):
        def _work():
            self.engine.press(key)
            try:
                self._note_playback_chrome(self.engine.refresh_playback())
            except Exception:
                pass

        self._run_bg(_work)

    def _toggle_power(self):
        key = self.engine.mark_power_optimistic()
        if self.page == "remote":
            self._apply_chrome_face()

        def _work():
            self.engine.press(key)
            try:
                self.engine.query_device_info()
                self._note_playback_chrome(self.engine.refresh_playback())
            except Exception:
                pass

        self._run_bg(_work)

    def _launch(self, app):
        app_id = app.get("id", "")
        self.selected_app_id = str(app_id or "")
        if self.page == "apps":
            self._build_page()

        def _work():
            self.engine.launch_refresh(app_id)
            try:
                self._note_playback_chrome(self.engine.refresh_playback())
            except Exception:
                pass

        self._run_bg(_work)

    def _refresh_apps(self):
        self.page = "apps"
        self.app_offset = 0
        self._set_status("loading apps...")
        self._build_page()

        def _work():
            self.engine.query_apps()
            n = len(self.engine.store_apps())
            self._queue_status(("%d apps" % n) if n else (self.engine.last_error or "no apps"))
            self._pending_rebuild = True

        self._run_bg(_work)

    def _refresh_playback_bg(self):
        def _work():
            try:
                line = self.engine.refresh_playback()
            except Exception:
                line = self.engine.playback_status()
            self._note_playback_chrome(line, force_rebuild=False)
            self._pending_chrome = True

        self._run_bg(_work)

    def _show_dev_info(self):
        def _work():
            info = self.engine.query_device_info()
            line = (info.get("model-name", "") + " " + info.get("power-mode", "")).strip()
            self._queue_status(line or self.engine.last_error or "no info")

        self._set_status("dev info...")
        self._run_bg(_work)

    def _show_media(self):
        def _work():
            self._queue_status(self.engine.refresh_playback() or "no media")

        self._set_status("media...")
        self._run_bg(_work)

    def _show_tv_channel(self):
        def _work():
            raw = self.engine.query_tv_active_channel() or self.engine.query_tv_channels()
            self._queue_status((raw.replace("\n", " ")[:48]) if raw else "n/a")

        self._set_status("tv ch...")
        self._run_bg(_work)

    def _show_perf(self):
        def _work():
            raw = self.engine.query_chanperf()
            self._queue_status((raw.replace("\n", " ")[:48]) if raw else (self.engine.last_error or "perf n/a"))

        self._set_status("perf...")
        self._run_bg(_work)

    # ----- Select page (cached TVs) + explicit Scan -----------------------

    def _merge_device_lists(self, *lists):
        by_host = {}
        by_serial = {}
        for lst in lists:
            for item in lst or []:
                host = ((item or {}).get("host") or "").strip()
                if not host:
                    continue
                serial = ((item or {}).get("serial") or "").strip()
                name = ((item or {}).get("name") or "").strip()
                if serial and serial in by_serial:
                    old = by_serial[serial]
                    old_host = (old.get("host") or "").strip()
                    if old_host and old_host != host:
                        by_host.pop(old_host, None)
                prev = by_host.get(host) or {}
                row = {
                    "host": host,
                    "name": name or prev.get("name") or "",
                    "serial": serial or prev.get("serial") or "",
                }
                by_host[host] = row
                if row["serial"]:
                    by_serial[row["serial"]] = row
        rows = list(by_host.values())
        rows.sort(key=lambda r: (r.get("name") or r.get("host") or "").lower())
        return rows

    def _open_select(self, soft_refresh=True):
        self._delete_armed = None
        self.discover_list = self._merge_device_lists(
            self.engine.cached_devices(), self.discover_list
        )
        self.page = "devices"
        self._build_page()
        n = len(self.discover_list)
        self._set_status(("%d saved" % n) if n else "no TVs - press Scan")
        if not soft_refresh:
            return

        def _work():
            try:
                devices = self.engine.refresh_cached_names()
            except Exception:
                devices = self.engine.cached_devices()
            self._pending_select_list = devices
            n2 = len(devices or [])
            self._queue_status(("%d saved" % n2) if n2 else "no TVs - press Scan")

        self._run_bg(_work)

    def _status_max_chars(self):
        """Character budget for the top status band (full width on Select)."""
        cw = max(6, (self.btn_text * 6) // 10)
        return max(8, (self.W - 2 * self.pad) // cw)

    def _arm_delete(self, dev):
        host = ((dev or {}).get("host") or "").strip()
        if not host:
            return
        name = ascii_label(((dev or {}).get("name") or "").strip() or host)
        self._delete_armed = host
        self._set_status(
            format_delete_status_chars(name, self._status_max_chars(), tail=" Scan")
        )

    def _scan_button(self):
        host = self._delete_armed
        if host:
            self._delete_armed = None
            try:
                self.engine.forget_device(host)
            except Exception:
                pass
            self.discover_list = [
                d for d in (self.discover_list or []) if (d.get("host") or "") != host
            ]
            self._set_status("deleted")
            self._build_page()
            return
        self._start_scan()

    def _pick_device(self, dev):
        host = (dev or {}).get("host") or ""
        name = ((dev or {}).get("name") or "").strip() or host
        if not host:
            self._set_status("no host")
            return
        self._delete_armed = None
        self.engine.set_host(host)
        self.ip_buf = host
        self.app_offset = 0
        self.page = "remote"
        self._set_status(name)
        self._build_page()

        def _work():
            ok = self.engine.connect(discover_if_empty=False)
            if ok:
                self._queue_status(self.engine.playback_status())
            else:
                self._queue_status(
                    self.engine.last_error or "unreachable - Scan or delete"
                )
            self._pending_rebuild = True

        self._run_bg(_work)

    def _start_scan(self):
        if self._scan_busy:
            return
        self._delete_armed = None
        self._scan_busy = True
        self._pending_devices = []
        self.page = "devices"
        self._set_status("Scanning...")
        self._build_page()
        # Defer discover so the Select page can paint first.
        self._scan_yield = True
        self._pending_scan = True

    def _paint_now(self):
        try:
            tick = getattr(self.display, "tick", None)
            if tick is not None:
                tick()
        except Exception:
            pass

    def _run_scan_work(self):
        self._paint_now()

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
                    timeout=3.0,
                    retries=1,
                    ssdp=True,
                    scan_fallback=True,
                    on_device=_on_device,
                )
                for dev in devices or []:
                    _on_device(dev)
                merged = self._merge_device_lists(
                    self.discover_list, self._pending_devices, devices
                )
                self._pending_select_list = merged
                if not merged:
                    self._queue_status(self.engine.last_error or "no Roku found")
                else:
                    self._queue_status("found %d - pick one" % len(merged))
            except Exception as e:
                self._queue_status(str(e))
            finally:
                self._scan_busy = False

        self._run_bg(_work)

    # ----- input + soft pump ---------------------------------------------

    def _on_key(self, sender, event):
        ecp = _KEY_MAP.get(getattr(event, "key", None))
        if ecp:
            self._ecp(ecp)

    def _pump(self, _=None):
        # Apply worker results on the main tick so the render loop is never
        # mutated from a worker thread.
        if self._pending_scan:
            if self._scan_yield:
                self._scan_yield = False
            else:
                self._pending_scan = False
                self._run_scan_work()

        if self._pending_status is not None:
            self.status.value = self._pending_status
            self._pending_status = None

        if self._pending_chrome:
            self._pending_chrome = False
            if self.page == "remote":
                self._apply_chrome_face()

        if self._pending_select_list is not None:
            self.discover_list = self._merge_device_lists(
                self.discover_list, self._pending_select_list
            )
            self._pending_select_list = None
            if self.page == "devices":
                self._build_page()

        if self._pending_devices and self.page == "devices":
            batch = self._pending_devices
            self._pending_devices = []
            before = {d.get("host") for d in self.discover_list}
            self.discover_list = self._merge_device_lists(self.discover_list, batch)
            after = {d.get("host") for d in self.discover_list}
            if after != before or self._scan_busy:
                self._build_page()

        if self._pending_rebuild:
            self._pending_rebuild = False
            self._build_page()

        self._status_ticks += 1
        # ~1s (pump is 250ms): keep app / state / position in sync.
        if (
            self.page == "remote"
            and (self.engine.host or "").strip()
            and self._status_ticks % 4 == 0
            and not self._playback_busy
        ):
            self._playback_busy = True

            def _work():
                try:
                    self._note_playback_chrome(self.engine.refresh_playback())
                except Exception:
                    pass
                self._playback_busy = False

            self._run_bg(_work)


def create(engine=None, start_page="devices"):
    """Build the pdwidgets front end (does not call ``run_forever``)."""
    return _RemoteUI(engine=engine, start_page=start_page)


def run(engine=None, start_page="devices"):
    """Create the UI and hand control to ``runtime.run_forever()``."""
    create(engine=engine, start_page=start_page)
    board_config.runtime.run_forever()


# Direct import / example kit: auto-start. ``roku_remote`` owns launch when set.
import roku_engine as _roku_engine  # noqa: E402

if not getattr(_roku_engine, "_LAUNCHER_OWNS_RUN", False):
    run()
