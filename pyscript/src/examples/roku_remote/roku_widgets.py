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
:class:`roku_engine.RokuEngine`. Remote chrome matches ``roku_lvgl``: utility,
D-pad, options (replay / info / CC), transport, volume, channel, then
APPS | MORE | SELECT. MORE lists TV inputs. Layout, padding, and text scales
are derived from ``display.width`` / ``height`` so the UI scales from 320x480
up through tall phone portraits.

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
    app_label,
    ascii_label,
    format_delete_status,
    format_switch_status,
    other_frontends,
    restart_app,
    set_frontend,
)
from roku_sim import make_engine

pd.DEBUG = False

FRONTEND = "widgets"

# Only the remote page is kept across navigations. Devices / Apps / More are
# built on entry and dropped on leave — MicroPython fragments badly if those
# trees stay live with raised Buttons.
_CACHED_PAGES = ("remote",)


def _shade(c, factor):
    """Darken (``factor`` < 1) or lighten (``factor`` > 1) an RGB565 color."""
    r = (c >> 8) & 0xF8
    g = (c >> 3) & 0xFC
    b = (c << 3) & 0xF8
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


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
        self.progress_h = 2
        # Match roku_graphics / LVGL: one 16px romfont scale for plaque + buttons.
        # 320→1; 480+→2 (unit//280 alone stays 1 until 560).
        self.btn_text = 16
        self.text_sm = 16
        self.text_14 = 14  # two-line plaque status (romfont MEDIUM)
        self.text_scale = max(1, self.unit // 280) + (1 if self.unit >= 400 else 0)
        self.name_h = self.btn_text * self.text_scale
        self.sm_h = self.name_h
        # Tall enough for two scaled plaque rows (and at least H/8 like LVGL).
        self.plaque_h = max(
            64,
            self.H // 8,
            self.btn_text * self.text_scale * 2 + 4 * self.pad,
        )

        # Dark remote palette (mirrors the graphics "midnight" chassis).
        self.BG = pal.color565(0x12, 0x14, 0x1A)
        self.STATUS_BG = pal.color565(0x1C, 0x22, 0x2E)
        self.PLAQUE_EDGE = pal.color565(0x2A, 0x31, 0x40)
        self.KEY_BG = pal.color565(0x3A, 0x40, 0x4E)
        self.ALT_BG = pal.color565(0x2E, 0x34, 0x40)
        self.ACCENT_BG = pal.color565(0x7C, 0x5C, 0xFC)
        self.ACCENT2 = pal.color565(0x5A, 0x3E, 0xD0)
        self.POWER_BG = pal.color565(0xE0, 0x5A, 0x4A)
        self.TRANSPORT_BG = pal.color565(0x3A, 0x5A, 0x72)
        self.UI_BG = pal.color565(0x24, 0x28, 0x34)
        self.TEXT = pal.color565(0xF2, 0xF4, 0xF8)
        self.MUTED = pal.color565(0x9A, 0xA0, 0xB0)
        self.ON_ACCENT = pal.color565(0xFF, 0xFF, 0xFF)

        self.engine = engine if engine is not None else make_engine()
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
        self._pending_state = None
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
        self._scan_full = False
        self._pending_scan = False
        self._scan_yield = False
        self._press_t0 = 0
        self._press_dev = None
        self._page_panels = {}
        self._page_parent = None

        self.screen = pd.Screen(self.display, bg=self.BG, visible=False)
        plaque_w = self.W - 2 * self.pad
        self.progress_w = plaque_w
        self._status_time_reserve = max(48, self.unit // 4)
        self._status_inner_pad = self.pad

        # Persistent plaque (name / state / status / time) — not rebuilt per page.
        self.plaque = pd.Widget(
            self.screen,
            x=self.pad,
            y=self.pad,
            w=plaque_w,
            h=self.plaque_h,
            align=pd.ALIGN.TOP_LEFT,
            bg=self.STATUS_BG,
            padding=(0, 0, 0, 0),
        )
        half_h = max(1, self.plaque_h // 2)
        y_top = max(2, (half_h - self.name_h) // 2)
        y_bot = self._plaque_status_y(1)

        # Transparent label bg so a wide TL name cannot erase TR state when the
        # plaque redraws (children paint in set order; opaque fills would stack).
        self.name_lbl = pd.Label(
            self.plaque,
            value="Roku Remote",
            x=self.pad,
            y=y_top,
            align=pd.ALIGN.TOP_LEFT,
            fg=self.TEXT,
            text_height=self.btn_text,
            scale=self.text_scale,
            padding=(0, 0, 0, 0),
        )
        self.state_lbl = pd.Label(
            self.plaque,
            value="",
            x=-self.pad,
            y=y_top,
            align=pd.ALIGN.TOP_RIGHT,
            fg=self.MUTED,
            text_height=self.text_sm,
            scale=self.text_scale,
            padding=(0, 0, 0, 0),
        )
        self.status_lbl = pd.Label(
            self.plaque,
            value="",
            x=self.pad,
            y=y_bot,
            w=max(40, plaque_w // 2),
            h=self.sm_h * 2,
            align=pd.ALIGN.TOP_LEFT,
            fg=self.MUTED,
            text_height=self.text_sm,
            scale=self.text_scale,
            padding=(0, 0, 0, 0),
        )
        self.time_lbl = pd.Label(
            self.plaque,
            value="",
            x=-self.pad,
            y=y_bot,
            align=pd.ALIGN.TOP_RIGHT,
            fg=self.MUTED,
            text_height=self.text_sm,
            scale=self.text_scale,
            padding=(0, 0, 0, 0),
        )
        self._layout_status_width(reserve_time=(self.page != "devices"))

        gap_y = max(1, (self.pad - self.progress_h) // 2)
        self.progress_track = pd.Widget(
            self.screen,
            x=self.pad,
            y=self.pad + self.plaque_h + gap_y,
            w=plaque_w,
            h=self.progress_h,
            align=pd.ALIGN.TOP_LEFT,
            bg=self.PLAQUE_EDGE,
            padding=(0, 0, 0, 0),
            visible=False,
        )
        self.progress_fill = pd.Widget(
            self.progress_track,
            x=0,
            y=0,
            w=0,
            h=self.progress_h,
            align=pd.ALIGN.TOP_LEFT,
            bg=self.TRANSPORT_BG,
            padding=(0, 0, 0, 0),
        )

        # Content below plaque + pads (progress sits in the pad gap, like LVGL).
        chrome_h = self.plaque_h + 2 * self.pad
        self.content = pd.Widget(
            self.screen,
            w=self.W,
            h=self.H - chrome_h,
            align=pd.ALIGN.BOTTOM,
            bg=self.BG,
            padding=(0, 0, 0, 0),
        )

        self.screen.add_event_cb(pd.events.KEYDOWN, self._on_key)

        self.screen.visible = True

        # Soft pump: apply worker results + periodic playback refresh on main tick.
        self._pump_timer = Timer(-1)
        try:
            self._pump_timer.init(
                mode=Timer.PERIODIC, period=250, callback=self._pump, hard=False
            )
        except Exception:
            pass

        # Build only the page we will show (lazy panels keep the rest cold).
        if self.page == "remote" and (self.engine.host or "").strip():
            self._show_page("remote", rebuild=True)
            name = ""
            try:
                name = (self.engine.device_info or {}).get("user-device-name") or ""
            except Exception:
                pass
            self._set_name(name or self.engine.host or "Roku")
            self._set_state("")
            self._set_status(self.engine.playback_app_label() or "ready")
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

    def _measure_lbl(self, height=None):
        """Label for width probes (single face/scale; any plaque label works)."""
        if height == self.btn_text and self.name_lbl is not None:
            return self.name_lbl
        return self.status_lbl

    def _text_px(self, text, height=None):
        """Pixel width of one line via ``Label.text_width`` (no draw)."""
        return self._measure_lbl(height).text_width(text or "")

    def _wrap_text(self, text, max_w, height=None, max_lines=0):
        """Word-wrap ``text`` to ``max_w`` pixels; optional ``max_lines`` cap."""
        s = text or ""
        if max_w <= 0 or not s:
            return s
        measure = self._measure_lbl(height).text_width
        words = s.replace("\n", " ").split()
        if not words:
            return s
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else (cur + " " + word)
            if measure(trial) <= max_w:
                cur = trial
                continue
            if cur:
                lines.append(cur)
                if max_lines and len(lines) >= max_lines:
                    return "\n".join(lines)
                cur = ""
            if measure(word) <= max_w:
                cur = word
                continue
            # Hard-break an overlong token.
            chunk = ""
            for ch in word:
                trial = chunk + ch
                if chunk and measure(trial) > max_w:
                    lines.append(chunk)
                    if max_lines and len(lines) >= max_lines:
                        return "\n".join(lines)
                    chunk = ch
                else:
                    chunk = trial
            cur = chunk
        if cur and not (max_lines and len(lines) >= max_lines):
            lines.append(cur)
        return "\n".join(lines)

    def _status_face(self, nlines=1):
        """Romfont height for BL status: text14 when two lines, else text16."""
        return self.text_14 if int(nlines or 1) >= 2 else self.btn_text

    def _status_line_h(self, nlines=1):
        return self._status_face(nlines) * self.text_scale

    def _plaque_status_y(self, nlines=1):
        """Y for BL status so ``nlines`` stay inside the plaque.

        Two-line prompts sit just under TL (room between name and plaque bottom).
        Single-line keeps the lower-half placement.
        """
        nlines = max(1, min(2, int(nlines or 1)))
        line_h = self._status_line_h(nlines)
        block_h = line_h * nlines
        gap = max(2, self.pad)
        y_below_name = self.name_h + gap
        y_bottom = self.plaque_h - block_h - gap
        if nlines >= 2:
            return y_below_name if y_below_name <= y_bottom else max(2, y_bottom)
        half_h = max(1, self.plaque_h // 2)
        y_pref = half_h + max(2, (half_h - line_h) // 2)
        return max(y_below_name, min(y_pref, y_bottom))

    def _fit_label(self, lbl, text, _height=None):
        """Set label text and resize to measured width (RIGHT align keeps edge)."""
        if lbl is None:
            return
        s = text if text is not None else ""
        tw = max(1, lbl.text_width(s))
        lbl.value = s
        lbl.set_position(w=tw, h=lbl.char_height)
        # Clear old glyphs under transparent labels.
        if self.plaque is not None:
            self.plaque.invalidate()

    def _layout_status_width(self, reserve_time=True, nlines=1):
        """Size the bottom-left status label; Select reclaims the time column."""
        if self.status_lbl is None:
            return
        plaque_w = self.W - 2 * self.pad
        reserve = self._status_time_reserve if reserve_time else 0
        inner = self._status_inner_pad
        w = max(40, plaque_w - 2 * inner - reserve)
        nlines = max(1, min(2, int(nlines or 1)))
        face = self._status_face(nlines)
        line_h = face * self.text_scale
        if self.status_lbl.text_height != face:
            self.status_lbl.text_height = face
        y = self._plaque_status_y(nlines)
        self.status_lbl.set_position(x=self.pad, y=y, w=w, h=line_h * nlines)
        if self.time_lbl is not None:
            # Keep BR clock on the first status line.
            self.time_lbl.set_position(y=y)

    def _status_avail_width(self):
        """Pixel width available for status text."""
        if self.status_lbl is not None:
            try:
                w = int(self.status_lbl.width)
                if w > 0:
                    return w
            except Exception:
                pass
        plaque_w = self.W - 2 * self.pad
        reserve = 0 if self.page == "devices" else self._status_time_reserve
        return max(40, plaque_w - 2 * self._status_inner_pad - reserve)

    def _queue_status(self, line):
        if line is None:
            return
        # Preserve newlines for two-line prompts (delete / switch confirm).
        if "\n" in line:
            self._pending_status = "\n".join(ascii_label(p) for p in line.split("\n"))
        else:
            self._pending_status = ascii_label(line)

    def _queue_state(self, line):
        if line is not None:
            self._pending_state = ascii_label(line)

    def _queue_playback_plaque(self):
        """Queue bottom-left app + top-right state from the latest engine probe."""
        self._queue_status(self.engine.playback_app_label())
        self._queue_state(self.engine.playback_state_label())

    def _set_name(self, line):
        text = ascii_label(line or "Roku Remote")
        # Prefer a long TL name; TR state is usually a short token. If TR is
        # ever wide, its opaque bg may overpaint the name (accepted).
        reserve = self._text_px("buffering") + self.pad
        max_w = max(40, self.plaque.width - 2 * self.pad - reserve)
        while len(text) > 1 and self._text_px(text, self.btn_text) > max_w:
            text = text[:-1]
        self._fit_label(self.name_lbl, text)

    def _set_state(self, line):
        self._fit_label(self.state_lbl, ascii_label(line if line is not None else ""))

    def _set_time(self, line):
        self._fit_label(self.time_lbl, ascii_label(line if line is not None else ""))

    def _set_progress_visible(self, visible):
        if self.progress_track is None:
            return
        self.progress_track.visible = bool(visible)

    def _update_progress(self):
        """Under-plaque scrub rail from position/duration (hidden when unusable)."""
        if self.progress_track is None or self.progress_fill is None:
            return
        frac = self.engine.progress_fraction()
        if frac is None:
            self._set_progress_visible(False)
            self.progress_fill.set_position(w=0, h=self.progress_h)
            return
        self._set_progress_visible(True)
        w = int(self.progress_w * frac + 0.5)
        if w < 0:
            w = 0
        if w > self.progress_w:
            w = self.progress_w
        self.progress_fill.set_position(w=w, h=self.progress_h)

    def _set_status(self, line):
        """Bottom-left plaque: app name or user feedback (Scanning, Netflix, …)."""
        on_select = self.page == "devices"
        full_width = on_select or bool(getattr(self, "_switch_armed", None))
        raw = line if line is not None else ""
        if "\n" in raw:
            parts = [ascii_label(p) for p in raw.split("\n")]
        else:
            parts = [ascii_label(raw)]
        # Width first (may reclaim time column), then wrap, then place by line count.
        self._layout_status_width(reserve_time=not full_width, nlines=1)
        max_w = self._status_avail_width()
        wrapped_parts = []
        for p in parts:
            if self._text_px(p) <= max_w:
                wrapped_parts.append(p)
            else:
                wrapped_parts.append(self._wrap_text(p, max_w, max_lines=2))
        text = "\n".join(wrapped_parts)
        lines = text.split("\n")[:2]
        text = "\n".join(lines)
        nlines = max(1, len(lines)) if text else 1
        self._layout_status_width(reserve_time=not full_width, nlines=nlines)
        if self.status_lbl is not None:
            self.status_lbl.value = text
            if self.plaque is not None:
                self.plaque.invalidate()
        if on_select:
            self._set_time("")
            self._set_progress_visible(False)
            return
        self._set_time(self.engine.position_label())
        self._update_progress()

    def _clear_content(self):
        """Drop all lazy page panels (full reset)."""
        for name in list(self._page_panels.keys()):
            self._drop_page(name)
        self.content.invalidate()

    def _gc(self):
        try:
            import gc

            gc.collect()
        except Exception:
            pass

    def _drop_page(self, name):
        """Destroy one cached page panel so the next show rebuilds it."""
        panel = self._page_panels.pop(name, None)
        if panel is None:
            return
        if name == "remote":
            self._play_btn = None
            self._power_btn = None
        # Detach children first so dirty sets / event closures can drop.
        for child in list(getattr(panel, "children", ()) or ()):
            try:
                panel.remove_child(child)
            except Exception:
                pass
        try:
            self.content.remove_child(panel)
        except Exception:
            pass
        self._gc()

    def _trim_page_cache(self, keep):
        """Keep ``keep`` plus a hidden ``remote`` panel; drop everything else."""
        for name in list(self._page_panels.keys()):
            if name == keep:
                continue
            if name in _CACHED_PAGES:
                continue
            self._drop_page(name)

    def _page_panel(self, name):
        panel = self._page_panels.get(name)
        if panel is not None:
            return panel
        panel = pd.Widget(
            self.content,
            x=0,
            y=0,
            w=self.content.width,
            h=self.content.height,
            align=pd.ALIGN.TOP_LEFT,
            bg=self.BG,
            padding=(0, 0, 0, 0),
            visible=False,
        )
        self._page_panels[name] = panel
        return panel

    def _show_page(self, name, rebuild=False):
        """Show ``name``; only ``remote`` is retained when navigating away."""
        cacheable = name in _CACHED_PAGES
        panel = self._page_panels.get(name)
        # Non-cached pages always rebuild so Select/Apps/More never accumulate.
        need = (not cacheable) or rebuild or panel is None or not panel.children
        if need:
            if panel is not None:
                self._drop_page(name)
            panel = self._page_panel(name)
            self._page_parent = panel
            self.page = name
            try:
                if name == "devices":
                    self._build_devices()
                elif name == "apps":
                    self._build_apps()
                elif name == "more":
                    self._build_more()
                else:
                    self._build_remote()
            finally:
                self._page_parent = None
        self.page = name
        for n, p in self._page_panels.items():
            p.visible = n == name
        self._trim_page_cache(name)
        self.content.invalidate()

    def _button_parent(self):
        return self._page_parent if self._page_parent is not None else self.content

    def _colors_for(self, role):
        """Return ``(text, face, bg_hi, bg_lo, rim)`` matching ``roku_graphics`` roles."""
        if role == "accent":
            face = self.ACCENT_BG
            return (
                self.ON_ACCENT,
                face,
                _shade(face, 1.15),
                self.ACCENT2,
                _shade(face, 0.55),
            )
        if role == "power":
            face = self.POWER_BG
            return (
                self.TEXT,
                face,
                _shade(face, 1.12),
                _shade(face, 0.75),
                _shade(face, 0.55),
            )
        if role == "transport":
            face = self.TRANSPORT_BG
            return (
                self.TEXT,
                face,
                _shade(face, 1.12),
                _shade(face, 0.8),
                _shade(face, 0.55),
            )
        if role == "alt":
            face = self.ALT_BG
            return (
                self.TEXT,
                face,
                _shade(face, 1.1),
                _shade(face, 0.8),
                _shade(face, 0.55),
            )
        if role == "ui":
            face = self.UI_BG
            return (
                self.MUTED,
                face,
                _shade(face, 1.1),
                _shade(face, 0.8),
                _shade(face, 0.55),
            )
        face = self.KEY_BG
        return (
            self.TEXT,
            face,
            _shade(face, 1.12),
            _shade(face, 0.78),
            _shade(face, 0.55),
        )

    def _apply_wrapped_label(self, btn, label, height=None):
        """Wrap a button's label and center the text block in the tile."""
        lab = getattr(btn, "label", None)
        if lab is None:
            return
        face = self.btn_text if height is None else height
        max_w = max(8, int(btn.width) - 2 * max(2, self.pad))
        wrapped = self._wrap_text(label, max_w, face, max_lines=3)
        measure = lab.text_width
        lines = wrapped.split("\n") if wrapped else [""]
        line_ws = [measure(ln) for ln in lines]
        block_w = max(line_ws) if line_ws else 1
        # Romfont: pad shorter lines with spaces so each line is centered in
        # the block (framebuf.text is left-aligned within the label).
        space_w = max(1, measure(" "))
        centered = []
        for ln, lw in zip(lines, line_ws):
            pad = max(0, (block_w - lw) // (2 * space_w))
            centered.append((" " * pad) + ln)
        lab.value = "\n".join(centered)
        lab.set_position(
            w=max(1, block_w),
            h=lab.char_height * len(lines),
            align=pd.ALIGN.CENTER,
            align_to=btn,
        )

    def _button(self, label, x, y, w, h, on_click, role="key", wrap=False, round_btn=False):
        fg, bg, bg_hi, bg_lo, rim = self._colors_for(role)
        rad = (min(int(w), int(h)) // 2) if round_btn else self.radius
        btn = pd.Button(
            self._button_parent(),
            label=label,
            x=int(x),
            y=int(y),
            w=int(w),
            h=int(h),
            radius=rad,
            fg=bg,
            bg=bg,
            text_color=fg,
            text_height=self.btn_text,
            scale=self.text_scale,
            shadow=0,
            style="raised",
            bg_hi=bg_hi,
            bg_lo=bg_lo,
            rim=rim,
        )
        if wrap:
            self._apply_wrapped_label(btn, label)

        def _cb(sender, event, _fn=on_click):
            _fn()

        btn.add_event_cb(pd.events.MOUSEBUTTONUP, _cb)
        return btn

    def _device_button(self, label, x, y, w, h, dev, role="key"):
        """Select-page TV row: short tap picks, long-press arms delete."""
        fg, bg, bg_hi, bg_lo, rim = self._colors_for(role)
        btn = pd.Button(
            self._button_parent(),
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
            scale=self.text_scale,
            shadow=0,
            style="raised",
            bg_hi=bg_hi,
            bg_lo=bg_lo,
            rim=rim,
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
        """Rebuild the current page panel (data changed)."""
        self._show_page(self.page, rebuild=True)

    def _place3(self, x0, y, w, row_h, gap, specs):
        """Place three equal-width buttons (LVGL ``_place3`` parity)."""
        bw = (w - 2 * gap) // 3
        out = []
        for i, (lab, role, on_click) in enumerate(specs):
            out.append(
                self._button(lab, x0 + i * (bw + gap), y, bw, row_h, on_click, role)
            )
        return out

    def _build_remote(self):
        """Match ``roku_lvgl._build_remote``: 6 rows + circular D-pad."""
        parent = self._button_parent()
        W = parent.width
        H = parent.height
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        if H < 80:
            H = max(80, self.H - self.plaque_h - 2 * self.pad)

        gaps = 7 * gap
        ring = max(150, int(min(w * 0.6, H * 0.34)))
        row_h = max(38, (H - ring - gaps) // 6)
        leftover = H - ring - gaps - 6 * row_h
        if leftover > 0:
            row_h += leftover // 6

        y = pad

        # 1) Utility: BACK | HOME | PWR
        util = self._place3(
            x0,
            y,
            w,
            row_h,
            gap,
            (
                ("BACK", "key", lambda: self._ecp("Back")),
                ("HOME", "accent", lambda: self._ecp("Home")),
                ("PWR " + self.engine.power_label(), "power", self._toggle_power),
            ),
        )
        self._power_btn = util[2] if len(util) > 2 else None
        y += row_h + gap

        # 2) Circular D-pad (round arrows + OK on a 3x3 grid)
        dx = x0 + (w - ring) // 2
        cell = max(1, ring // 3)
        margin = max(2, min(self.pad, cell // 6))
        arrow = max(1, cell - 2 * margin)
        cx = dx + ring // 2
        cy = y + ring // 2

        def _round_at(lab, ox, oy, size, role, on_click):
            self._button(
                lab,
                cx + ox - size // 2,
                cy + oy - size // 2,
                size,
                size,
                on_click,
                role,
                round_btn=True,
            )

        _round_at("^", 0, -cell, arrow, "key", lambda: self._ecp("Up"))
        _round_at("v", 0, cell, arrow, "key", lambda: self._ecp("Down"))
        _round_at("<", -cell, 0, arrow, "key", lambda: self._ecp("Left"))
        _round_at(">", cell, 0, arrow, "key", lambda: self._ecp("Right"))
        _round_at("OK", 0, 0, cell, "accent", lambda: self._ecp("Select"))
        y += ring + gap

        # 3) Options: RPL | * | CC
        self._place3(
            x0,
            y,
            w,
            row_h,
            gap,
            (
                ("RPL", "alt", lambda: self._ecp("InstantReplay")),
                ("*", "alt", lambda: self._ecp("Info")),
                ("CC", "alt", lambda: self._ecp("ClosedCaption")),
            ),
        )
        y += row_h + gap

        # 4) Transport
        play_face = self.engine.play_label()
        self._chrome_face = "%s|%s" % (play_face, self.engine.power_label())
        trans = self._place3(
            x0,
            y,
            w,
            row_h,
            gap,
            (
                ("<<", "transport", lambda: self._ecp("Rev")),
                (play_face, "transport", lambda: self._ecp("Play")),
                (">>", "transport", lambda: self._ecp("Fwd")),
            ),
        )
        self._play_btn = trans[1] if len(trans) > 1 else None
        y += row_h + gap

        # 5) Volume
        self._place3(
            x0,
            y,
            w,
            row_h,
            gap,
            (
                ("VOL-", "key", lambda: self._ecp("VolumeDown")),
                ("MUTE", "alt", lambda: self._ecp("VolumeMute")),
                ("VOL+", "key", lambda: self._ecp("VolumeUp")),
            ),
        )
        y += row_h + gap

        # 6) Channel
        self._place3(
            x0,
            y,
            w,
            row_h,
            gap,
            (
                ("CH-", "key", lambda: self._ecp("ChannelDown")),
                ("ENT", "alt", lambda: self._ecp("Enter")),
                ("CH+", "key", lambda: self._ecp("ChannelUp")),
            ),
        )
        y += row_h + gap

        # 7) Chrome: APPS | MORE | SELECT
        self._place3(
            x0,
            y,
            w,
            row_h,
            gap,
            (
                ("APPS", "ui", self._open_apps),
                ("MORE", "ui", self._open_more),
                ("SELECT", "ui", self._open_select),
            ),
        )

    def _build_devices(self):
        parent = self._button_parent()
        W = parent.width
        H = parent.height
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(40, H // 11)
        third = (w - 2 * gap) // 3
        self._button("REMOTE", x0, pad, third, row_h, self._goto_remote, "ui")
        self._button(
            "SCAN",
            x0 + third + gap,
            pad,
            third,
            row_h,
            self._scan_button,
            "accent",
        )
        self._button(
            "FULL",
            x0 + 2 * (third + gap),
            pad,
            third,
            row_h,
            self._full_scan_button,
            "accent",
        )
        y = pad + row_h + gap
        slot_h = max(44, self.plaque_h - 2 * pad)
        devices = self.discover_list or []
        avail = H - y - pad
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
        parent = self._button_parent()
        W = parent.width
        H = parent.height
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(40, H // 11)
        third = (w - 2 * gap) // 3
        self._button("REMOTE", x0, pad, third, row_h, self._goto_remote, "ui")
        self._button("REFRESH", x0 + third + gap, pad, third, row_h, self._refresh_apps, "ui")
        self._button("NEXT", x0 + 2 * (third + gap), pad, third, row_h, self._apps_next, "ui")
        y = pad + row_h + gap

        cols = 3
        bw = (w - gap * (cols - 1)) // cols
        bh = bw
        avail = H - y - pad
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
            name = app_label(app.get("name") or app.get("id") or "?")
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
                wrap=True,
            )

    def _build_more(self):
        """MORE: REMOTE + other frontends; TV inputs grid (LVGL parity)."""
        parent = self._button_parent()
        W = parent.width
        H = parent.height
        pad = self.pad
        gap = pad
        x0 = pad
        w = W - 2 * pad
        row_h = max(40, H // 11)
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
        avail = H - y - pad
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
                wrap=True,
            )

    # ----- navigation -----------------------------------------------------

    def _goto(self, page):
        self._show_page(page, rebuild=False)
        if page == "remote":
            # Always re-probe — clears sticky apps/inputs plaque text and
            # recovers from a false "offline" after a transient error.
            self._refresh_playback_bg()

    def _arm_switch(self, frontend):
        self._switch_armed = frontend
        self._layout_status_width(reserve_time=False)
        avail = self._status_avail_width()

        def fits(s):
            first = s.split("\n", 1)[0]
            return self._text_px(first) <= avail

        self._set_status(format_switch_status(frontend, fits=fits, tail="\npress REMOTE"))

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
        msg = restart_app()
        if msg:
            self._set_status(msg)
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
        self.app_offset = 0
        if not self.selected_app_id:
            self.selected_app_id = str((self.engine.active_app or {}).get("id") or "")
        if self.engine.apps:
            self._set_status("%d apps" % len(self.engine.store_apps()))
            self._show_page("apps", rebuild=True)
        else:
            self._refresh_apps()

    def _apps_next(self):
        n = len(self.engine.store_apps())
        step = max(1, int(self.app_page_size or 1))
        if n:
            self.app_offset = (self.app_offset + step) % n
        self._show_page("apps", rebuild=True)

    # ----- ECP actions ----------------------------------------------------

    def _set_btn_label(self, btn, text):
        if btn is None:
            return
        lab = getattr(btn, "label", None)
        if lab is None:
            return
        try:
            s = ascii_label(text)
            lab.value = s
            lab.set_position(
                w=max(1, lab.text_width(s)),
                h=lab.char_height,
                align=pd.ALIGN.CENTER,
                align_to=btn,
            )
            btn.invalidate()
        except Exception:
            pass

    def _apply_chrome_face(self):
        play_face = self.engine.play_label()
        power_face = self.engine.power_label()
        self._chrome_face = "%s|%s" % (play_face, power_face)
        self._set_btn_label(self._play_btn, play_face)
        self._set_btn_label(self._power_btn, "PWR " + power_face)

    def _note_playback_chrome(self, force_rebuild=False):
        """Mailbox plaque (app + state) and in-place play/power chrome."""
        self._queue_playback_plaque()
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
        # Always re-apply play/power faces after a probe (not only on change) so
        # Pause/Play matches LVGL even when the face string was already correct
        # in cache or the first refresh races the TV.
        self._chrome_face = face
        self._pending_chrome = True

    def _ecp(self, key):
        def _work():
            self.engine.press(key)
            try:
                self.engine.refresh_playback()
                self._note_playback_chrome()
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
                self.engine.refresh_playback()
                self._note_playback_chrome()
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
                self.engine.refresh_playback()
                self._note_playback_chrome()
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
                self.engine.refresh_playback()
            except Exception:
                pass
            self._note_playback_chrome(force_rebuild=False)
            self._pending_chrome = True

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
        self._show_page("devices", rebuild=True)
        n = len(self.discover_list)
        self._set_status(("%d saved" % n) if n else "no TVs - press Scan")
        self._set_state("")
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

    def _arm_delete(self, dev):
        host = ((dev or {}).get("host") or "").strip()
        if not host:
            return
        name = ascii_label(((dev or {}).get("name") or "").strip() or host)
        self._delete_armed = host
        self._layout_status_width(reserve_time=False)
        avail = self._status_avail_width()

        def fits(s):
            first = s.split("\n", 1)[0]
            return self._text_px(first) <= avail

        self._set_status(format_delete_status(name, fits, tail="\npress Scan"))

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
        self._start_scan(full=False)

    def _full_scan_button(self):
        """Select FULL: disarm delete and run SSDP + cache + unicast /24."""
        self._delete_armed = None
        self._start_scan(full=True)

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
        self._set_name(name)
        self._set_state("")
        self.page = "remote"
        self._build_page()

        def _work():
            ok = self.engine.connect(discover_if_empty=False)
            if ok:
                self._queue_playback_plaque()
            else:
                self._queue_status(
                    self.engine.last_error or "unreachable - Scan or delete"
                )
            self._pending_rebuild = True

        self._run_bg(_work)

    def _start_scan(self, full=False):
        if self._scan_busy:
            return
        self._delete_armed = None
        self._scan_busy = True
        self._scan_full = bool(full)
        self._pending_devices = []
        self.page = "devices"
        self._set_status("Full scan..." if full else "Scanning...")
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
        scan_fallback = bool(getattr(self, "_scan_full", False))

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
                    scan_fallback=scan_fallback,
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
            self._set_status(self._pending_status)
            self._pending_status = None

        if self._pending_state is not None:
            self._set_state(self._pending_state)
            self._pending_state = None

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
        # ~1s (pump is 250ms): keep app / state / position[/duration] in sync.
        if (
            self.page == "remote"
            and (self.engine.host or "").strip()
            and self._status_ticks % 4 == 0
            and not self._playback_busy
        ):
            self._playback_busy = True

            def _work():
                try:
                    self.engine.refresh_playback()
                    self._note_playback_chrome()
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
