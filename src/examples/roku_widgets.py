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

Edit ``ROKU_HOST`` below, or leave empty and use SCAN / the IP pad on device.
Requires Roku **Control by mobile apps -> Enabled**. Join WiFi before running
on a microcontroller.
"""

import sys

_EXAMPLES = __file__.replace("\\", "/").rsplit("/", 1)[0]
if _EXAMPLES not in sys.path:
    sys.path.insert(0, _EXAMPLES)

import board_config
import pdwidgets as pd
from eventsys.keys import Keys
from multimer import Timer
from roku_engine import ROKU_HOST as _DEFAULT_HOST
from roku_engine import RokuEngine, ascii_label

pd.DEBUG = False

# Override here, or leave "" and use SCAN / IP pad.
ROKU_HOST = _DEFAULT_HOST

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

    def __init__(self):
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

        self.engine = RokuEngine(host=ROKU_HOST)
        self.ip_buf = self.engine.host or ""
        self.page = "devices"
        self.app_offset = 0
        self.app_page_size = 1
        self.discover_list = []

        # Cross-thread mailboxes (worker writes, soft pump applies on main tick).
        self._pending_status = None
        self._pending_devices = []
        self._pending_rebuild = False
        self._playback_busy = False
        self._status_ticks = 0
        self._scan_busy = False

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

        self._start_scan()

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

    # ----- page building --------------------------------------------------

    def _build_page(self):
        self._clear_content()
        if self.page == "devices":
            self._build_devices()
        elif self.page == "apps":
            self._build_apps()
        elif self.page == "more":
            self._build_more()
        elif self.page == "ip":
            self._build_ip()
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
        self._button(
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

        # Mid row: REPLAY | * | SRCH
        bw = (w - 2 * gap) // 3
        self._button("REPLAY", x0, y, bw, row_h, lambda: self._ecp("InstantReplay"), "key")
        self._button("*", x0 + bw + gap, y, bw, row_h, lambda: self._ecp("Info"), "key")
        self._button("SRCH", x0 + 2 * (bw + gap), y, bw, row_h, lambda: self._ecp("Search"), "key")
        y += row_h + gap

        # Transport: << | PLAY | >>
        self._button("<<", x0, y, bw, row_h, lambda: self._ecp("Rev"), "transport")
        self._button(
            self.engine.play_label(),
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

        # Chrome: APPS | MORE | SCAN
        bh = max(30, row_h - 4)
        self._button("APPS", x0, y, bw, bh, self._open_apps, "ui")
        self._button("MORE", x0 + bw + gap, y, bw, bh, lambda: self._goto("more"), "ui")
        self._button("SCAN", x0 + 2 * (bw + gap), y, bw, bh, self._rescan, "ui")

    def _build_devices(self):
        W = self.content.width
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(34, self.content.height // 12)
        self._button("REMOTE", x0, pad, (w - gap) // 2, row_h, lambda: self._goto("remote"), "ui")
        self._button(
            "RESCAN", x0 + (w - gap) // 2 + gap, pad, (w - gap) // 2, row_h, self._rescan, "accent"
        )
        y = pad + row_h + gap
        slot_h = max(34, self.status_h)
        devices = self.discover_list or []
        avail = self.content.height - y - pad
        max_slots = max(1, (avail + gap) // (slot_h + gap))
        for i, dev in enumerate(devices[:max_slots]):
            label = ascii_label((dev.get("name") or "").strip() or "Roku")
            self._button(
                label,
                x0,
                y + i * (slot_h + gap),
                w,
                slot_h,
                (lambda d=dev: self._pick_device(d)),
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
        self._button("REMOTE", x0, pad, third, row_h, lambda: self._goto("remote"), "ui")
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
        apps = self.engine.apps or []
        window = apps[self.app_offset : self.app_offset + max_slots]
        for i, app in enumerate(window):
            name = ascii_label(app.get("name") or app.get("id") or "?")
            col = i % cols
            row = i // cols
            self._button(
                name,
                x0 + col * (bw + gap),
                y + row * (bh + gap),
                bw,
                bh,
                (lambda a=app: self._launch(a)),
                "accent" if i == 0 else "key",
            )

    def _build_more(self):
        W = self.content.width
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(34, self.content.height // 12)
        half = (w - gap) // 2
        self._button("REMOTE", x0, pad, half, row_h, lambda: self._goto("remote"), "ui")
        self._button("IP", x0 + half + gap, pad, half, row_h, lambda: self._goto("ip"), "ui")
        y = pad + row_h + gap
        actions = (
            ("DEV INFO", self._show_dev_info),
            ("MEDIA", self._show_media),
            ("TV CH", self._show_tv_channel),
            ("PERF", self._show_perf),
        )
        for i, (lab, fn) in enumerate(actions):
            col = i % 2
            row = i // 2
            self._button(
                lab,
                x0 + col * (half + gap),
                y + row * (row_h + gap),
                half,
                row_h,
                fn,
                "key",
            )

    def _build_ip(self):
        W = self.content.width
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(34, self.content.height // 12)
        third = (w - 2 * gap) // 3
        self._button("BACK", x0, pad, third, row_h, lambda: self._goto("more"), "ui")
        self._button("CLR", x0 + third + gap, pad, third, row_h, self._ip_clear, "ui")
        self._button("SET", x0 + 2 * (third + gap), pad, third, row_h, self._ip_set, "accent")
        y = pad + row_h + gap
        shown = self.ip_buf if self.ip_buf else "(empty)"
        self._button(shown, x0, y, w, row_h, lambda: None, "alt")
        y += row_h + gap
        keys = "123456789.0<"
        cols = 3
        bw = (w - gap * (cols - 1)) // cols
        for i, ch in enumerate(keys):
            col = i % cols
            row = i // cols
            lab = "BS" if ch == "<" else ch
            self._button(
                lab,
                x0 + col * (bw + gap),
                y + row * (row_h + gap),
                bw,
                row_h,
                (lambda c=ch: self._ip_key(c)),
                "key",
            )

    # ----- navigation -----------------------------------------------------

    def _goto(self, page):
        self.page = page
        self._build_page()
        if page == "remote" and self.engine.connected:
            self._refresh_playback_bg()

    def _open_apps(self):
        self.page = "apps"
        self.app_offset = 0
        if self.engine.apps:
            self._set_status("%d apps" % len(self.engine.apps))
            self._build_page()
        else:
            self._refresh_apps()

    def _apps_next(self):
        n = len(self.engine.apps or [])
        step = max(1, int(self.app_page_size or 1))
        if n:
            self.app_offset = (self.app_offset + step) % n
        self._build_page()

    # ----- ECP actions ----------------------------------------------------

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
            self._build_page()

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
        self.page = "apps"
        self.app_offset = 0
        self._set_status("loading apps...")
        self._build_page()

        def _work():
            self.engine.query_apps()
            n = len(self.engine.apps or [])
            self._queue_status(("%d apps" % n) if n else (self.engine.last_error or "no apps"))
            self._pending_rebuild = True

        self._run_bg(_work)

    def _refresh_playback_bg(self):
        def _work():
            try:
                self._queue_status(self.engine.refresh_playback())
            except Exception:
                pass

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

    # ----- IP entry -------------------------------------------------------

    def _ip_clear(self):
        self.ip_buf = ""
        self._build_page()

    def _ip_key(self, ch):
        if ch == "<":
            self.ip_buf = self.ip_buf[:-1]
        elif len(self.ip_buf) < 15:
            self.ip_buf += ch
        self._build_page()

    def _ip_set(self):
        self.engine.set_host(self.ip_buf)
        self.app_offset = 0
        self._set_status("connecting " + (self.ip_buf or "?"))
        self.page = "remote"
        self._build_page()

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
        self.page = "remote"
        self._set_status(name)
        self._build_page()

        def _work():
            self.engine.connect(discover_if_empty=False)
            self._queue_status(self.engine.playback_status())
            self._pending_rebuild = True

        self._run_bg(_work)

    def _rescan(self):
        self.page = "devices"
        self.discover_list = []
        self._pending_devices = []
        self._set_status("Scanning...")
        self._build_page()
        self._start_scan()

    def _start_scan(self):
        if self._scan_busy:
            return
        self._scan_busy = True

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
                if not (devices or self._pending_devices):
                    self._queue_status(self.engine.last_error or "no Roku found")
                else:
                    self._queue_status("found %d - pick one" % len(self._pending_devices))
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
        if self._pending_status is not None:
            self.status.value = self._pending_status
            self._pending_status = None

        if self._pending_devices and self.page == "devices":
            known = {d.get("host") for d in self.discover_list}
            new = [d for d in self._pending_devices if d.get("host") not in known]
            if new:
                self.discover_list.extend(new)
                self._build_page()

        if self._pending_rebuild:
            self._pending_rebuild = False
            self._build_page()

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


remote = _RemoteUI()

# Canonical entry: pdwidgets wired input + rendering into the shared runtime at
# Display construction, so this just keeps the app alive.
board_config.runtime.run_forever()
