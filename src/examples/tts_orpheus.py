# gallery: skip
# deps: lvgl
"""LVGL textarea → local Orpheus-3B TTS → board_config.audio_out.

Needs ``tts``, a reachable Orpheus OpenAI-compatible bridge
(``secrets.ORPHEUS_BASE_URL``, default ``http://127.0.0.1:5005/v1``), and
``board_config`` with lazy ``audio_out`` in ``DEVICES``.

Host stack: load
https://huggingface.co/isaiahbjork/orpheus-3b-0.1-ft-Q4_K_M-GGUF
in LM Studio, then run an Orpheus FastAPI bridge (e.g. Orpheus-FastAPI-LMStudio
on ``:5005``). See::

    https://pydevices.github.io/micropython-hardware/audio.html#orpheus-lm-studio

Voice catalog comes from ``OrpheusTTS.voices()``. Put emotion tags in Style or
Text (``<laugh>``, ``<sigh>``, …); Style is prepended to the spoken line.
"""

import display_driver  # noqa: F401 — wires LVGL flush + input + event_loop
import lvgl as lv
import board_config as bc

from tts import OrpheusTTS, TTSClient

try:
    from secrets import ORPHEUS_BASE_URL
except ImportError:
    ORPHEUS_BASE_URL = "http://127.0.0.1:5005/v1"

DEFAULT_TEXT = "Hello from MicroPython. <laugh> Local Orpheus text to speech is working."
DEFAULT_STYLE = ""

# Studio palette (ink + amber). Avoids default LVGL grey chrome.
_C_BG = 0x0E1419
_C_BG2 = 0x1A2430
_C_PANEL = 0x1C2834
_C_PANEL_HI = 0x243442
_C_BORDER = 0x3A5166
_C_TEXT = 0xE8EEF2
_C_MUTED = 0x8A9AAB
_C_ACCENT = 0xE8A54B
_C_ACCENT_DIM = 0xB87A28
_C_OK = 0x6FCF97
_C_ERR = 0xE07A6A

_provider = OrpheusTTS(base_url=ORPHEUS_BASE_URL)
_client = TTSClient(_provider, chunk_size=4096)
_status = None
_speak_btn = None
_voice_dd = None
_style_ta = None
_text_ta = None
_voice_labels = []
_retry_timer = None
_retry_left = 0


def _color(rgb):
    return lv.color_hex(rgb)


def _font_for(size):
    """Largest compiled Montserrat at or below ``size`` (points)."""
    size = max(1, int(size))
    for points in (48, 40, 36, 32, 28, 24, 22, 20, 18, 16, 14, 12):
        if points <= size:
            font = getattr(lv, "font_montserrat_%d" % points, None)
            if font is not None:
                return font, points
    for points in (12, 14, 16, 18, 20, 22, 24, 28, 32, 36, 40, 48):
        font = getattr(lv, "font_montserrat_%d" % points, None)
        if font is not None:
            return font, points
    return None, 0


def _set_font(obj, target_size):
    """Set text font only (safe for sized widgets like textarea)."""
    font, _points = _font_for(target_size)
    if font is not None:
        obj.set_style_text_font(font, 0)


def _set_scaled_font(obj, target_size):
    """Nearest compiled font, scaled to ``target_size`` visual points."""
    font, points = _font_for(target_size)
    if font is None:
        return
    obj.set_style_text_font(font, 0)
    scale = max(128, min(640, round(256 * int(target_size) / points)))
    if scale == 256:
        return
    try:
        obj.set_style_transform_scale(scale, 0)
    except AttributeError:
        obj.set_style_transform_scale_x(scale, 0)
        obj.set_style_transform_scale_y(scale, 0)


def _refresh_ui():
    """Force a paint so UI updates show before blocking I/O (HTTP / audio)."""
    inst = display_driver.event_loop.current_instance()
    lv.screen_active().invalidate()
    try:
        lv.refr_now(lv.display_get_default())
    except TypeError:
        lv.refr_now(None)
    display_driver._present_next_ok_ms = None
    if inst is not None:
        inst.task_handler()
    display_driver._present_lvgl_displays()


def _dd_selected_text(dd, options):
    idx = dd.get_selected()
    if 0 <= idx < len(options):
        return options[idx]
    return options[0] if options else ""


def _speak_options():
    """Build kwargs for TTSClient.speak from the LVGL controls."""
    opts = {
        "voice": OrpheusTTS.voice_from_label(_dd_selected_text(_voice_dd, _voice_labels)),
    }
    style = (_style_ta.get_text() if _style_ta is not None else "").strip()
    if style:
        # Prepended into the spoken text (emotion tags / stage directions).
        opts["instructions"] = style
    return opts


def _retry_seconds(exc):
    """Parse 'Please retry in N.NNs' style delays, or None."""
    msg = str(exc)
    key = "retry in "
    i = msg.lower().find(key)
    if i < 0:
        return None
    num = []
    for ch in msg[i + len(key) :]:
        if ch.isdigit() or ch == ".":
            num.append(ch)
        elif num:
            break
    if not num:
        return None
    try:
        return max(1, int(float("".join(num))))
    except ValueError:
        return None


def _status_for_error(exc):
    """Short status line when there is no parseable retry delay."""
    msg = str(exc)
    lower = msg.lower()
    if "connection" in lower or "econn" in lower or "timed out" in lower:
        return "Orpheus bridge unreachable"
    if len(msg) > 80:
        return msg[:77] + "..."
    return msg


def _set_status(text, tone="muted", refresh=True):
    if _status is None:
        return
    _status.set_text(text)
    colors = {"muted": _C_MUTED, "accent": _C_ACCENT, "ok": _C_OK, "err": _C_ERR}
    _status.set_style_text_color(_color(colors.get(tone, _C_MUTED)), 0)
    if refresh:
        _refresh_ui()


def _set_speak_enabled(enabled):
    if _speak_btn is None:
        return
    if enabled:
        _speak_btn.remove_state(lv.STATE.DISABLED)
    else:
        _speak_btn.add_state(lv.STATE.DISABLED)


def _stop_retry_timer():
    global _retry_timer, _retry_left
    if _retry_timer is not None:
        try:
            _retry_timer.delete()
        except TypeError:
            try:
                _retry_timer.delete(None)
            except Exception:
                pass
        except Exception:
            pass
        _retry_timer = None
    _retry_left = 0


def _retry_tick(_t):
    """lv.timer callback: count down quota wait, then re-enable Speak."""
    global _retry_left
    _retry_left -= 1
    if _retry_left <= 0:
        _stop_retry_timer()
        _set_status("Ready - tap Speak", "muted", refresh=False)
        _set_speak_enabled(True)
        return
    # No _refresh_ui here — avoid re-entering task_handler from a timer.
    _set_status("Please retry in %d seconds." % _retry_left, "err", refresh=False)


def _start_retry_countdown(secs):
    global _retry_timer, _retry_left
    _stop_retry_timer()
    _retry_left = max(1, int(secs))
    _set_speak_enabled(False)
    _set_status("Please retry in %d seconds." % _retry_left, "err")
    _retry_timer = lv.timer_create(_retry_tick, 1000, None)


def speak(text=None):
    if _retry_left > 0:
        return 0
    if text is None and _text_ta is not None:
        text = _text_ta.get_text()
    text = (text or "").strip()
    if not text:
        return 0
    if "audio_out" not in bc.DEVICES:
        raise RuntimeError("board_config has no audio_out in DEVICES")
    _set_speak_enabled(False)
    _set_status("Speaking...", "accent")
    output = bc.audio_out
    set_vol = getattr(output, "set_volume", None)
    if set_vol is not None:
        set_vol(85)
    try:
        total = _client.speak(text, output, **_speak_options())
    except Exception as exc:
        # Never re-raise from the LVGL click handler — that stalls the UI.
        wait = _retry_seconds(exc)
        if wait is not None:
            print("tts_orpheus: retry in %d s" % wait)
            _start_retry_countdown(wait)
        else:
            msg = _status_for_error(exc)
            _set_status(msg, "err")
            _set_speak_enabled(True)
            print("tts_orpheus:", msg)
        return 0
    finally:
        output.close()
    _set_status("Done (%d bytes)" % total, "ok")
    _set_speak_enabled(True)
    return total


def _style_screen(scr):
    scr.set_style_bg_color(_color(_C_BG), 0)
    scr.set_style_bg_grad_color(_color(_C_BG2), 0)
    scr.set_style_bg_grad_dir(lv.GRAD_DIR.VER, 0)
    scr.set_style_bg_opa(lv.OPA.COVER, 0)


def _style_field(obj, radius):
    obj.set_style_radius(radius, 0)
    obj.set_style_bg_color(_color(_C_PANEL), 0)
    obj.set_style_bg_opa(lv.OPA.COVER, 0)
    obj.set_style_border_color(_color(_C_BORDER), 0)
    obj.set_style_border_width(1, 0)
    obj.set_style_pad_all(max(6, radius // 2), 0)
    obj.set_style_text_color(_color(_C_TEXT), 0)
    # Focused: warm accent rim.
    obj.set_style_border_color(_color(_C_ACCENT), lv.STATE.FOCUSED)
    obj.set_style_border_width(2, lv.STATE.FOCUSED)


def _style_dropdown(dd, radius):
    _style_field(dd, radius)
    dd.set_style_bg_color(_color(_C_PANEL_HI), 0)
    lst = dd.get_list() if hasattr(dd, "get_list") else None
    if lst is None:
        return
    lst.set_style_radius(radius, 0)
    lst.set_style_bg_color(_color(_C_PANEL), 0)
    lst.set_style_bg_opa(lv.OPA.COVER, 0)
    lst.set_style_border_color(_color(_C_ACCENT_DIM), 0)
    lst.set_style_border_width(1, 0)
    lst.set_style_text_color(_color(_C_TEXT), 0)
    selected = getattr(lv, "PART", None)
    selected = getattr(selected, "SELECTED", None) if selected is not None else None
    if selected is not None:
        lst.set_style_bg_color(_color(_C_ACCENT_DIM), selected)
        lst.set_style_text_color(_color(_C_TEXT), selected)


def _style_button(btn, radius):
    btn.set_style_radius(radius, 0)
    btn.set_style_bg_color(_color(_C_ACCENT), 0)
    btn.set_style_bg_grad_color(_color(_C_ACCENT_DIM), 0)
    btn.set_style_bg_grad_dir(lv.GRAD_DIR.VER, 0)
    btn.set_style_bg_opa(lv.OPA.COVER, 0)
    btn.set_style_border_width(0, 0)
    btn.set_style_shadow_color(_color(_C_ACCENT), 0)
    btn.set_style_shadow_width(max(6, radius), 0)
    btn.set_style_shadow_opa(90, 0)
    btn.set_style_shadow_offset_y(max(2, radius // 4), 0)
    # Pressed: flatten / darken.
    btn.set_style_bg_color(_color(_C_ACCENT_DIM), lv.STATE.PRESSED)
    btn.set_style_shadow_width(2, lv.STATE.PRESSED)
    # Disabled (quota cooldown): muted flat panel.
    btn.set_style_bg_color(_color(_C_PANEL_HI), lv.STATE.DISABLED)
    btn.set_style_bg_grad_color(_color(_C_PANEL), lv.STATE.DISABLED)
    btn.set_style_shadow_width(0, lv.STATE.DISABLED)
    btn.set_style_text_color(_color(_C_MUTED), lv.STATE.DISABLED)


def _add_label(parent, text, body_pt, y, w, pad):
    lbl = lv.label(parent)
    lbl.set_text(text.upper() if len(text) < 28 else text)
    _set_font(lbl, max(12, body_pt - 4))
    lbl.set_style_text_color(_color(_C_MUTED), 0)
    lbl.set_style_text_letter_space(1, 0)
    lbl.set_width(w - 2 * pad)
    lbl.align(lv.ALIGN.TOP_LEFT, pad, y)
    return lbl


def _set_dropdown_font(dd, target_size, box_w, box_h):
    """Larger text on the closed control and the open list.

    When only a smaller Montserrat bitmap is compiled, scale the closed
    control but shrink its layout size so the visual still fits ``box_*``.
    """
    font, points = _font_for(target_size)
    if font is None:
        dd.set_size(box_w, box_h)
        return
    dd.set_style_text_font(font, 0)
    scale = max(128, min(640, round(256 * int(target_size) / points)))
    if scale != 256:
        # Visual size ≈ layout * scale/256 — invert so it lands in the box.
        dd.set_size(max(1, (box_w * 256) // scale), max(1, (box_h * 256) // scale))
        for setter, args in (
            ("set_style_transform_pivot_x", (0, 0)),
            ("set_style_transform_pivot_y", (0, 0)),
        ):
            fn = getattr(dd, setter, None)
            if fn is not None:
                fn(*args)
        try:
            dd.set_style_transform_scale(scale, 0)
        except AttributeError:
            dd.set_style_transform_scale_x(scale, 0)
            dd.set_style_transform_scale_y(scale, 0)
    else:
        dd.set_size(box_w, box_h)
    lst = dd.get_list() if hasattr(dd, "get_list") else None
    if lst is None:
        return
    lst.set_style_text_font(font, 0)
    pad_row = max(8, int(target_size) // 2)
    if hasattr(lst, "set_style_pad_row"):
        lst.set_style_pad_row(pad_row, 0)
    if hasattr(lst, "set_style_text_line_space"):
        lst.set_style_text_line_space(pad_row // 2, 0)
    if hasattr(lst, "set_style_pad_ver"):
        lst.set_style_pad_ver(pad_row // 2, 0)
    if hasattr(lst, "set_style_max_height"):
        lst.set_style_max_height(box_h * 8, 0)


def _add_dropdown(parent, options, selected, ctrl_pt, y, w, pad, row_h, radius):
    dd = lv.dropdown(parent)
    dd.set_options("\n".join(options))
    try:
        idx = options.index(selected)
    except ValueError:
        idx = 0
    dd.set_selected(idx)
    box_w = w - 2 * pad
    dd.align(lv.ALIGN.TOP_LEFT, pad, y)
    _set_dropdown_font(dd, ctrl_pt, box_w, row_h)
    _style_dropdown(dd, radius)
    return dd


# Build UI with the LVGL event loop paused (same pattern as lvgl_test.py).
_inst = display_driver.event_loop.current_instance()
if _inst is not None:
    _inst.disable()
try:
    scr = lv.screen_active()
    w, h = scr.get_width(), scr.get_height()
    unit = min(w, h)
    pad = max(10, unit // 40)
    title_pt = max(18, unit // 16)
    body_pt = max(14, unit // 22)
    # Dropdowns read small vs scaled labels; size them nearer the title.
    ctrl_pt = max(body_pt + 4, unit // 18)  # ~18 @ 320, ~40 @ 720
    row_h = max(48, ctrl_pt + pad * 2)
    label_h = max(18, body_pt + 4)
    style_h = max(body_pt * 3, unit // 10)
    btn_h = max(44, body_pt * 2 + pad)
    btn_w = max(140, min(w - 2 * pad, body_pt * 10))
    radius = max(8, unit // 48)

    _style_screen(scr)

    # Scrollable column so 320x480 still fits voice/style controls.
    form = lv.obj(scr)
    form.set_size(w, h)
    form.set_style_pad_all(0, 0)
    form.set_style_border_width(0, 0)
    form.set_style_bg_opa(0, 0)
    if hasattr(form, "set_scroll_dir"):
        form.set_scroll_dir(lv.DIR.VER)
    if hasattr(form, "add_flag"):
        form.add_flag(lv.obj.FLAG.SCROLLABLE)

    y = pad

    # Accent bar behind the title (broadcast / VU-meter cue).
    accent = lv.obj(form)
    accent.set_size(max(4, pad // 3), title_pt + pad // 4)
    accent.set_pos(pad, y)
    accent.set_style_radius(max(2, pad // 6), 0)
    accent.set_style_bg_color(_color(_C_ACCENT), 0)
    accent.set_style_bg_opa(lv.OPA.COVER, 0)
    accent.set_style_border_width(0, 0)
    for flag_name in ("CLICKABLE", "SCROLLABLE"):
        flag = getattr(lv.obj.FLAG, flag_name, None)
        if flag is None:
            continue
        for meth in ("clear_flag", "remove_flag"):
            fn = getattr(accent, meth, None)
            if fn is not None:
                try:
                    fn(flag)
                except Exception:
                    pass
                break

    title = lv.label(form)
    title.set_text("Orpheus TTS")
    title.set_style_text_color(_color(_C_TEXT), 0)
    _set_scaled_font(title, title_pt)
    title.align(lv.ALIGN.TOP_LEFT, pad + max(8, pad // 2), y)
    y += title_pt + pad // 2

    _status = lv.label(form)
    _status.set_text("Tap Speak to play the text")
    _status.set_width(w - 2 * pad)
    _status.set_style_text_color(_color(_C_MUTED), 0)
    _set_scaled_font(_status, body_pt)
    _status.align(lv.ALIGN.TOP_LEFT, pad, y)
    y += body_pt + pad

    _voice_labels = [OrpheusTTS.voice_label(n, d) for n, d in OrpheusTTS.voices()]
    default_voice = OrpheusTTS.voice_label(_provider.voice)

    _add_label(form, "Voice", body_pt, y, w, pad)
    y += label_h
    _voice_dd = _add_dropdown(
        form, _voice_labels, default_voice, ctrl_pt, y, w, pad, row_h, radius
    )
    y += row_h + pad // 2

    _add_label(form, "Style / emotion tags", body_pt, y, w, pad)
    y += label_h
    _style_ta = lv.textarea(form)
    _style_ta.set_text(DEFAULT_STYLE)
    _style_ta.set_size(w - 2 * pad, style_h)
    _set_font(_style_ta, body_pt)
    _style_field(_style_ta, radius)
    _style_ta.align(lv.ALIGN.TOP_LEFT, pad, y)
    y += style_h + pad // 2

    _add_label(form, "Text", body_pt, y, w, pad)
    y += label_h
    ta_h = max(body_pt * 5, h // 4)
    _text_ta = lv.textarea(form)
    _text_ta.set_text(DEFAULT_TEXT)
    _text_ta.set_size(w - 2 * pad, ta_h)
    _set_font(_text_ta, body_pt)
    _style_field(_text_ta, radius)
    _text_ta.align(lv.ALIGN.TOP_LEFT, pad, y)
    lv.group_focus_obj(_text_ta)
    y += ta_h + pad

    _speak_btn = lv.button(form)
    _speak_btn.set_size(btn_w, btn_h)
    _speak_btn.align(lv.ALIGN.TOP_MID, 0, y)
    _style_button(_speak_btn, max(radius, btn_h // 3))
    lbl = lv.label(_speak_btn)
    lbl.set_text("Speak")
    lbl.set_style_text_color(_color(_C_BG), 0)
    _set_scaled_font(lbl, body_pt)
    lbl.center()
    _speak_btn.add_event_cb(lambda _e: speak(), lv.EVENT.CLICKED, None)
    y += btn_h + pad
    if hasattr(form, "set_style_min_height"):
        form.set_style_min_height(y, 0)
finally:
    if _inst is not None:
        _inst.enable()

_refresh_ui()
print("tts_orpheus: ready - pick voice/style, then tap Speak")
# Returns immediately on an interactive REPL with machine.Timer / signals;
# blocks when launched as a named script (e.g. main.py boot).
display_driver.runtime.run_forever()
