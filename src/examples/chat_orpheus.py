# gallery: skip
# deps: lvgl
"""LVGL chat → Gemma (LM Studio) → Orpheus speaks the reply.

Orpheus-3B is TTS only. Chat answers come from Gemma in LM Studio
(``CHAT_MODEL``, default ``google/gemma-4-e4b``); Orpheus reads them aloud.

Secrets (optional overrides)::

    LM_STUDIO_BASE_URL = "http://192.168.1.10:1234/v1"
    CHAT_MODEL = "google/gemma-4-e4b"
    ORPHEUS_BASE_URL = "http://192.168.1.10:5005/v1"

Needs ``tts``, ``requests``, and ``board_config.audio_out``.
"""

import json

import display_driver  # noqa: F401 — wires LVGL flush + input + event_loop
import lvgl as lv
import board_config as bc

try:
    import requests
except ImportError:
    import urequests as requests

from tts import OrpheusTTS, TTSClient

try:
    from secrets import LM_STUDIO_BASE_URL
except ImportError:
    LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"

try:
    from secrets import CHAT_MODEL
except ImportError:
    CHAT_MODEL = "google/gemma-4-e4b"

try:
    from secrets import ORPHEUS_BASE_URL
except ImportError:
    ORPHEUS_BASE_URL = "http://127.0.0.1:5005/v1"

SYSTEM_PROMPT = (
    "You are a helpful assistant on a small embedded display. "
    "Answer clearly in at most three short sentences unless the user asks for more. "
    "Prefer plain speech that sounds natural when read aloud. "
    "Do not use markdown, bullet lists, or code fences."
)
MAX_HISTORY = 12  # user+assistant pairs capped via message list length
MAX_TOKENS = 180

# Studio palette (ink + amber) — match tts_* examples.
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
_C_USER = 0x2A3A4A

_provider = OrpheusTTS(base_url=ORPHEUS_BASE_URL)
_client = TTSClient(_provider, chunk_size=4096)
_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
_status = None
_send_btn = None
_voice_dd = None
_input_ta = None
_log = None
_voice_labels = []
_busy = False
_body_pt = 14
_pad = 10
_radius = 8
_bubble_w = 280


def _color(rgb):
    return lv.color_hex(rgb)


def _font_for(size):
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
    font, _points = _font_for(target_size)
    if font is not None:
        obj.set_style_text_font(font, 0)


def _set_scaled_font(obj, target_size):
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


def _set_status(text, tone="muted", refresh=True):
    if _status is None:
        return
    _status.set_text(text)
    colors = {"muted": _C_MUTED, "accent": _C_ACCENT, "ok": _C_OK, "err": _C_ERR}
    _status.set_style_text_color(_color(colors.get(tone, _C_MUTED)), 0)
    if refresh:
        _refresh_ui()


def _set_send_enabled(enabled):
    if _send_btn is None:
        return
    if enabled:
        _send_btn.remove_state(lv.STATE.DISABLED)
    else:
        _send_btn.add_state(lv.STATE.DISABLED)


def _trim_history():
    """Keep system + last MAX_HISTORY non-system messages."""
    global _messages
    sys_msg = _messages[0] if _messages and _messages[0].get("role") == "system" else None
    rest = [m for m in _messages if m is not sys_msg]
    if len(rest) > MAX_HISTORY:
        rest = rest[-MAX_HISTORY:]
    _messages = ([sys_msg] if sys_msg else []) + rest


def _add_bubble(role, text):
    """Append a chat bubble to the scrollable log."""
    if _log is None:
        return
    row = lv.obj(_log)
    row.set_width(lv.pct(100))
    row.set_height(lv.SIZE_CONTENT if hasattr(lv, "SIZE_CONTENT") else lv.SIZE.CONTENT)
    row.set_style_bg_opa(0, 0)
    row.set_style_border_width(0, 0)
    row.set_style_pad_all(0, 0)
    if hasattr(row, "clear_flag"):
        row.clear_flag(lv.obj.FLAG.SCROLLABLE)

    bubble = lv.obj(row)
    bubble.set_width(_bubble_w)
    bubble.set_height(lv.SIZE_CONTENT if hasattr(lv, "SIZE_CONTENT") else lv.SIZE.CONTENT)
    bubble.set_style_radius(_radius, 0)
    bubble.set_style_pad_all(max(6, _pad // 2), 0)
    bubble.set_style_border_width(0, 0)
    if role == "user":
        bubble.set_style_bg_color(_color(_C_USER), 0)
        bubble.align(lv.ALIGN.TOP_RIGHT, -_pad // 2, 0)
    else:
        bubble.set_style_bg_color(_color(_C_PANEL), 0)
        bubble.align(lv.ALIGN.TOP_LEFT, _pad // 2, 0)
    bubble.set_style_bg_opa(lv.OPA.COVER, 0)

    who = lv.label(bubble)
    who.set_text("You" if role == "user" else "Assistant")
    _set_font(who, max(10, _body_pt - 4))
    who.set_style_text_color(_color(_C_ACCENT if role == "user" else _C_MUTED), 0)

    body = lv.label(bubble)
    body.set_text(text)
    body.set_long_mode(lv.LABEL_LONG.WRAP if hasattr(lv, "LABEL_LONG") else lv.label.LONG.WRAP)
    body.set_width(_bubble_w - max(12, _pad))
    _set_font(body, _body_pt)
    body.set_style_text_color(_color(_C_TEXT), 0)
    body.align(lv.ALIGN.TOP_LEFT, 0, _body_pt + 4)

    if hasattr(_log, "scroll_to_view"):
        try:
            row.scroll_to_view(lv.ANIM.ON if hasattr(lv, "ANIM") else True)
        except TypeError:
            row.scroll_to_view(True)
    elif hasattr(_log, "scroll_to_y"):
        try:
            _log.scroll_to_y(lv.COORD_MAX if hasattr(lv, "COORD_MAX") else 32767, False)
        except Exception:
            pass
    _refresh_ui()


def _chat_completion(user_text):
    """POST /chat/completions; return assistant text or raise."""
    url = LM_STUDIO_BASE_URL.rstrip("/") + "/chat/completions"
    _messages.append({"role": "user", "content": user_text})
    _trim_history()
    body = json.dumps(
        {
            "model": CHAT_MODEL,
            "messages": _messages,
            "temperature": 0.5,
            "max_tokens": MAX_TOKENS,
            "stream": False,
        }
    )
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, data=body, headers=headers)
    try:
        status = getattr(resp, "status_code", 200)
        if status >= 400:
            detail = getattr(resp, "text", "") or str(status)
            raise RuntimeError("chat HTTP %s: %s" % (status, detail[:120]))
        raw = resp.content if hasattr(resp, "content") else resp.text
        if isinstance(raw, bytes):
            raw = raw.decode()
        data = json.loads(raw)
    finally:
        close = getattr(resp, "close", None)
        if close is not None:
            close()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("chat returned no choices")
    msg = choices[0].get("message") or {}
    text = (msg.get("content") or "").strip()
    if not text:
        raise RuntimeError("chat returned empty content")
    _messages.append({"role": "assistant", "content": text})
    _trim_history()
    return text


def _speak(text):
    if "audio_out" not in bc.DEVICES:
        raise RuntimeError("board_config has no audio_out in DEVICES")
    output = bc.audio_out
    set_vol = getattr(output, "set_volume", None)
    if set_vol is not None:
        set_vol(85)
    voice = OrpheusTTS.voice_from_label(_dd_selected_text(_voice_dd, _voice_labels))
    try:
        return _client.speak(text, output, voice=voice)
    finally:
        output.close()


def send(text=None):
    """Send the input line: chat completion, then Orpheus playback."""
    global _busy
    if _busy:
        return
    if text is None and _input_ta is not None:
        text = _input_ta.get_text()
    text = (text or "").strip()
    if not text:
        return
    _busy = True
    _set_send_enabled(False)
    if _input_ta is not None:
        _input_ta.set_text("")
    _add_bubble("user", text)
    _set_status("Thinking (%s)..." % CHAT_MODEL, "accent")
    try:
        reply = _chat_completion(text)
    except Exception as exc:
        msg = str(exc)
        if len(msg) > 80:
            msg = msg[:77] + "..."
        _set_status(msg, "err")
        _set_send_enabled(True)
        _busy = False
        print("chat_orpheus:", msg)
        return
    _add_bubble("assistant", reply)
    _set_status("Speaking...", "accent")
    try:
        total = _speak(reply)
        _set_status("Done (%d bytes)" % total, "ok")
    except Exception as exc:
        msg = str(exc)
        if "connection" in msg.lower() or "timed out" in msg.lower():
            msg = "Orpheus bridge unreachable"
        elif len(msg) > 80:
            msg = msg[:77] + "..."
        _set_status(msg, "err")
        print("chat_orpheus speak:", msg)
    _set_send_enabled(True)
    _busy = False


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
    btn.set_style_bg_color(_color(_C_ACCENT_DIM), lv.STATE.PRESSED)
    btn.set_style_shadow_width(2, lv.STATE.PRESSED)
    btn.set_style_bg_color(_color(_C_PANEL_HI), lv.STATE.DISABLED)
    btn.set_style_bg_grad_color(_color(_C_PANEL), lv.STATE.DISABLED)
    btn.set_style_shadow_width(0, lv.STATE.DISABLED)
    btn.set_style_text_color(_color(_C_MUTED), lv.STATE.DISABLED)


def _set_dropdown_font(dd, target_size, box_w, box_h):
    font, points = _font_for(target_size)
    if font is None:
        dd.set_size(box_w, box_h)
        return
    dd.set_style_text_font(font, 0)
    scale = max(128, min(640, round(256 * int(target_size) / points)))
    if scale != 256:
        dd.set_size(max(1, (box_w * 256) // scale), max(1, (box_h * 256) // scale))
        try:
            dd.set_style_transform_scale(scale, 0)
        except AttributeError:
            dd.set_style_transform_scale_x(scale, 0)
            dd.set_style_transform_scale_y(scale, 0)
    else:
        dd.set_size(box_w, box_h)


# Build UI with the LVGL event loop paused.
_inst = display_driver.event_loop.current_instance()
if _inst is not None:
    _inst.disable()
try:
    scr = lv.screen_active()
    w, h = scr.get_width(), scr.get_height()
    unit = min(w, h)
    _pad = max(10, unit // 40)
    title_pt = max(18, unit // 16)
    _body_pt = max(14, unit // 22)
    ctrl_pt = max(_body_pt + 2, unit // 20)
    row_h = max(40, ctrl_pt + _pad)
    input_h = max(_body_pt * 3, unit // 9)
    btn_h = max(44, _body_pt * 2 + _pad // 2)
    btn_w = max(100, min(w // 3, _body_pt * 8))
    _radius = max(8, unit // 48)
    _bubble_w = max(160, w - 3 * _pad)

    _style_screen(scr)

    y = _pad
    title = lv.label(scr)
    title.set_text("Orpheus Chat")
    title.set_style_text_color(_color(_C_TEXT), 0)
    _set_scaled_font(title, title_pt)
    title.align(lv.ALIGN.TOP_LEFT, _pad, y)
    y += title_pt + _pad // 3

    _status = lv.label(scr)
    _status.set_text("Ask a question — %s answers, Orpheus speaks" % CHAT_MODEL)
    _status.set_width(w - 2 * _pad)
    _status.set_long_mode(lv.LABEL_LONG.WRAP if hasattr(lv, "LABEL_LONG") else lv.label.LONG.WRAP)
    _status.set_style_text_color(_color(_C_MUTED), 0)
    _set_scaled_font(_status, max(12, _body_pt - 2))
    _status.align(lv.ALIGN.TOP_LEFT, _pad, y)
    y += _body_pt + _pad // 2

    _voice_labels = [OrpheusTTS.voice_label(n, d) for n, d in OrpheusTTS.voices()]
    default_voice = OrpheusTTS.voice_label(_provider.voice)
    vlab = lv.label(scr)
    vlab.set_text("VOICE")
    _set_font(vlab, max(12, _body_pt - 4))
    vlab.set_style_text_color(_color(_C_MUTED), 0)
    vlab.align(lv.ALIGN.TOP_LEFT, _pad, y)
    y += max(16, _body_pt)
    _voice_dd = lv.dropdown(scr)
    _voice_dd.set_options("\n".join(_voice_labels))
    try:
        _voice_dd.set_selected(_voice_labels.index(default_voice))
    except ValueError:
        _voice_dd.set_selected(0)
    _voice_dd.align(lv.ALIGN.TOP_LEFT, _pad, y)
    _set_dropdown_font(_voice_dd, ctrl_pt, w - 2 * _pad, row_h)
    _style_dropdown(_voice_dd, _radius)
    y += row_h + _pad // 2

    # Bottom composer height reserved so the log fills the middle.
    composer_h = input_h + btn_h + _pad * 2
    log_h = max(120, h - y - composer_h - _pad)

    _log = lv.obj(scr)
    _log.set_size(w - 2 * _pad, log_h)
    _log.align(lv.ALIGN.TOP_LEFT, _pad, y)
    _log.set_style_radius(_radius, 0)
    _log.set_style_bg_color(_color(_C_BG2), 0)
    _log.set_style_bg_opa(lv.OPA.COVER, 0)
    _log.set_style_border_color(_color(_C_BORDER), 0)
    _log.set_style_border_width(1, 0)
    _log.set_style_pad_all(_pad // 2, 0)
    _log.set_style_pad_row(_pad // 2, 0)
    if hasattr(_log, "set_flex_flow"):
        _log.set_flex_flow(lv.FLEX_FLOW.COLUMN)
    if hasattr(_log, "set_scroll_dir"):
        _log.set_scroll_dir(lv.DIR.VER)
    if hasattr(_log, "add_flag"):
        _log.add_flag(lv.obj.FLAG.SCROLLABLE)

    composer_y = y + log_h + _pad // 2
    _input_ta = lv.textarea(scr)
    _input_ta.set_text("")
    _input_ta.set_placeholder_text("Ask a question...")
    _input_ta.set_size(w - 2 * _pad, input_h)
    _set_font(_input_ta, _body_pt)
    _style_field(_input_ta, _radius)
    _input_ta.align(lv.ALIGN.TOP_LEFT, _pad, composer_y)
    lv.group_focus_obj(_input_ta)

    _send_btn = lv.button(scr)
    _send_btn.set_size(btn_w, btn_h)
    _send_btn.align(lv.ALIGN.TOP_MID, 0, composer_y + input_h + _pad // 2)
    _style_button(_send_btn, max(_radius, btn_h // 3))
    lbl = lv.label(_send_btn)
    lbl.set_text("Send")
    lbl.set_style_text_color(_color(_C_BG), 0)
    _set_scaled_font(lbl, _body_pt)
    lbl.center()
    _send_btn.add_event_cb(lambda _e: send(), lv.EVENT.CLICKED, None)

    _add_bubble(
        "assistant",
        "Hi — ask me anything. I answer with %s, then Orpheus reads it aloud." % CHAT_MODEL,
    )
finally:
    if _inst is not None:
        _inst.enable()

_refresh_ui()
print("chat_orpheus: ready — chat=%s speak=%s" % (CHAT_MODEL, ORPHEUS_BASE_URL))
display_driver.runtime.run_forever()
