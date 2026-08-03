# gallery: skip
# deps: lvgl
"""LVGL chat using Groq Llama 3.3 70B and Groq-hosted Orpheus speech.

Groq's OpenAI-compatible chat endpoint generates the answer; its speech endpoint
runs ``canopylabs/orpheus-v1-english`` to read the answer aloud.

Secrets (optional overrides)::

    GROQ_API_KEY = "your-key"
    GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"
    CHAT_TIMEOUT = 15

Needs ``tts``, ``requests``, and ``board_config.audio_out``.
"""

import json
from secrets import GROQ_API_KEY

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in the environment")

import board_config as bc
import display_driver  # noqa: F401 — wires LVGL flush + input + event_loop
import lvgl as lv

try:
    import requests
except ImportError:
    import urequests as requests

from stt import GroqSTT, STTClient
from tts import GroqTTS, TTSClient

from multimer import sleep_ms

CHAT_BASE_URL = "https://api.groq.com/openai/v1"

try:
    from secrets import GROQ_CHAT_MODEL as CHAT_MODEL
except ImportError:
    CHAT_MODEL = "llama-3.3-70b-versatile"

try:
    from secrets import CHAT_TIMEOUT
except ImportError:
    CHAT_TIMEOUT = 15

SYSTEM_PROMPT = (
    "You are a helpful assistant on a small embedded display. "
    "Answer clearly in no more than 190 characters. "
    "Prefer plain speech that sounds natural when read aloud. "
    "Do not use markdown, bullet lists, or code fences."
)
MAX_HISTORY = 12  # user+assistant pairs capped via message list length
MAX_TOKENS = 160
MAX_CHAT_ATTEMPTS = 2
MAX_TTS_ATTEMPTS = 3
TTS_RETRY_MS = 750
UI_SETTLE_MS = 350

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

_provider = GroqTTS(GROQ_API_KEY)
_client = TTSClient(_provider, chunk_size=4096)
_stt_client = STTClient(GroqSTT(GROQ_API_KEY), chunk_size=4096)
_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
_status = None
_send_btn = None
_voice_dd = None
_input_ta = None
_log = None
_voice_labels = []
_busy = False
_listening = False
_ui_jobs = []
_generation_paused = False
_body_pt = 14
_chat_pt = 18
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
    lv.screen_active().invalidate()
    try:
        lv.refr_now(lv.display_get_default())
    except TypeError:
        lv.refr_now(None)
    display_driver._present_next_ok_ms = None
    # refr_now() already renders and flushes. Present the panel exactly once;
    # task_handler() would invoke the event loop's present callback as well.
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


def _settle_ui():
    """Let pending paint and scroll animation finish before blocking I/O."""
    sleep_ms(UI_SETTLE_MS)
    _refresh_ui()


def _trim_history():
    """Keep system + last MAX_HISTORY non-system messages."""
    global _messages
    sys_msg = _messages[0] if _messages and _messages[0].get("role") == "system" else None
    rest = [m for m in _messages if m is not sys_msg]
    if len(rest) > MAX_HISTORY:
        rest = rest[-MAX_HISTORY:]
    _messages = ([sys_msg] if sys_msg else []) + rest


def _short_error(exc, fallback=None):
    """Return a compact status message suitable for the small display."""
    msg = str(exc).strip() or (fallback or exc.__class__.__name__)
    lower = msg.lower()
    errno = getattr(exc, "errno", None)
    if errno is None:
        args = getattr(exc, "args", ())
        errno = args[0] if args and isinstance(args[0], int) else None
    # ESP-IDF/lwIP reports DNS/network failures as negative getaddrinfo
    # values (notably -202), while Unix ports use positive errno values.
    if errno in (-202, -201, -200, 101, 113, 118) or any(
        marker in lower
        for marker in ("errno -202", "network is unreachable", "no route to host")
    ):
        return "No network - check Wi-Fi"
    if "connection" in lower or "econn" in lower or "timed out" in lower or "etimedout" in lower:
        return fallback or "Service unreachable"
    if len(msg) > 80:
        return msg[:77] + "..."
    return msg


def _display_text(text):
    """Map Unicode punctuation to glyphs available in the embedded font."""
    replacements = {
        "—": "-",
        "–": "-",
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        "•": "*",
        "\u00a0": " ",
    }
    result = []
    for char in str(text):
        if char in replacements:
            result.append(replacements[char])
        elif ord(char) < 128:
            result.append(char)
        else:
            result.append("?")
    return "".join(result)


def _add_bubble(role, text, refresh=True):
    """Append a chat bubble to the scrollable log."""
    if _log is None:
        return
    row = lv.obj(_log)
    row.set_width(lv.pct(100))
    row.set_height(lv.SIZE_CONTENT)
    row.set_style_bg_opa(0, 0)
    row.set_style_border_width(0, 0)
    row.set_style_pad_all(0, 0)
    row.set_flex_flow(lv.FLEX_FLOW.ROW)
    row.set_flex_align(
        lv.FLEX_ALIGN.END if role == "user" else lv.FLEX_ALIGN.START,
        lv.FLEX_ALIGN.CENTER,
        lv.FLEX_ALIGN.CENTER,
    )
    if hasattr(row, "clear_flag"):
        row.clear_flag(lv.obj.FLAG.SCROLLABLE)

    bubble = lv.obj(row)
    bubble.set_width(_bubble_w)
    bubble.set_height(lv.SIZE_CONTENT)
    bubble.set_style_radius(_radius, 0)
    bubble.set_style_pad_all(max(6, _pad // 2), 0)
    bubble.set_style_pad_row(max(2, _pad // 4), 0)
    bubble.set_style_border_width(0, 0)
    bubble.set_flex_flow(lv.FLEX_FLOW.COLUMN)
    if role == "user":
        bubble.set_style_bg_color(_color(_C_USER), 0)
    else:
        bubble.set_style_bg_color(_color(_C_PANEL), 0)
    bubble.set_style_bg_opa(lv.OPA.COVER, 0)

    who = lv.label(bubble)
    who.set_text("You" if role == "user" else "Assistant")
    _set_font(who, max(16, _chat_pt - 8))
    who.set_style_text_color(_color(_C_ACCENT if role == "user" else _C_MUTED), 0)

    body = lv.label(bubble)
    body.set_text(_display_text(text))
    body.set_long_mode(lv.label.LONG_MODE.WRAP)
    body.set_width(_bubble_w - max(12, _pad * 2))
    _set_font(body, _chat_pt)
    body.set_style_text_color(_color(_C_TEXT), 0)

    # SIZE_CONTENT bubbles do not have their final geometry until layout runs.
    # Calculate it now so scrolling uses the completed reply height, then jump
    # to the bottom in the same frame instead of starting an animation that
    # blocking network I/O would prevent from advancing.
    lv.obj.update_layout(_log)
    if hasattr(_log, "scroll_to_view"):
        try:
            row.scroll_to_view(lv.ANIM.OFF)
        except (AttributeError, TypeError):
            row.scroll_to_view(False)
    elif hasattr(_log, "scroll_to_y"):
        try:
            _log.scroll_to_y(lv.COORD_MAX if hasattr(lv, "COORD_MAX") else 32767, False)
        except Exception:
            pass
    if refresh:
        _refresh_ui()


def _chat_completion(user_text):
    """POST /chat/completions; return assistant text or raise."""
    url = CHAT_BASE_URL + "/chat/completions"
    previous_messages = list(_messages)
    _messages.append({"role": "user", "content": user_text})
    _trim_history()
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + GROQ_API_KEY,
    }
    try:
        text = ""
        finish_reason = None
        for attempt in range(MAX_CHAT_ATTEMPTS):
            body = json.dumps(
                {
                    "model": CHAT_MODEL,
                    "messages": _messages,
                    "temperature": 0.5,
                    "max_tokens": MAX_TOKENS * (attempt + 1),
                    "stream": False,
                }
            )
            resp = requests.post(url, data=body, headers=headers, timeout=CHAT_TIMEOUT)
            try:
                status = getattr(resp, "status_code", 200)
                raw = resp.content if hasattr(resp, "content") else resp.text
                if isinstance(raw, bytes):
                    raw = raw.decode()
                if status >= 400:
                    try:
                        error = (json.loads(raw) if raw else {}).get("error") or {}
                        detail = error.get("message") if isinstance(error, dict) else error
                    except (TypeError, ValueError):
                        detail = raw
                    raise RuntimeError("chat HTTP %s: %s" % (status, detail or "request failed"))
                data = json.loads(raw) if raw else {}
            finally:
                close = getattr(resp, "close", None)
                if close is not None:
                    close()
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("chat returned no choices")
            choice = choices[0]
            finish_reason = choice.get("finish_reason")
            msg = choice.get("message") or {}
            text = (msg.get("content") or "").strip()
            if text:
                break
        if not text:
            raise RuntimeError("chat returned empty content (%s)" % (finish_reason or "unknown"))
        _messages.append({"role": "assistant", "content": text})
        _trim_history()
        return text
    except Exception:
        # A failed turn must not become context for the next request.
        _messages[:] = previous_messages
        raise


def _stream_speech(text, voice):
    if "audio_out" not in bc.DEVICES:
        raise RuntimeError("board_config has no audio_out in DEVICES")
    output = bc.audio_out
    set_vol = getattr(output, "set_volume", None)
    if set_vol is not None:
        set_vol(85)
    stream = None
    try:
        for attempt in range(MAX_TTS_ATTEMPTS):
            try:
                stream = _client.stream(text, voice=voice)
                break
            except Exception as exc:
                message = str(exc)
                retryable = any(
                    "TTS HTTP %d" % status in message
                    for status in (500, 502, 503, 504)
                )
                if not retryable or attempt + 1 >= MAX_TTS_ATTEMPTS:
                    raise
                _set_status(
                    "Groq TTS busy - retrying %d/%d..."
                    % (attempt + 2, MAX_TTS_ATTEMPTS),
                    "accent",
                    refresh=True,
                )
                sleep_ms(TTS_RETRY_MS * (attempt + 1))
        if getattr(output, "format", stream.format) != stream.format:
            raise ValueError("audio output format does not match TTS format")
        total = 0
        first_chunk = True
        for chunk in stream:
            if not chunk:
                continue
            if first_chunk:
                _set_status("Speaking...", "accent", refresh=True)
                first_chunk = False
            total += output.write(chunk)
        if first_chunk:
            raise ValueError("Groq Orpheus response contained no audio")
        # machine.I2S has no queue-aware drain(). Push enough silence to move
        # the final speech beyond the ESP32 board's 20 kB DMA/ring buffer before
        # close() disables the amplifier and deinitializes the peripheral.
        padding = output.format.rate * output.format.frame_size // 2
        output.write(bytes(padding))
        drain = getattr(output, "drain", None)
        if drain is not None:
            drain()
        return total
    finally:
        if stream is not None:
            stream.close()
        output.close()


def _chat_reply_ready(value):
    global _generation_paused
    reply, voice = value
    _add_bubble("assistant", reply)
    _settle_ui()
    _set_status("Generating speech...", "accent")
    inst = display_driver.event_loop.current_instance()
    if inst is not None:
        inst.disable()
        _generation_paused = True
    try:
        total = _stream_speech(reply, voice)
    except Exception as exc:
        _turn_finished(("speak", exc))
        return
    _turn_finished(("done", total))


def _turn_finished(value):
    global _busy
    _resume_after_generation()
    kind, result = value
    if kind == "done":
        _set_status("Done (%d bytes)" % result, "ok")
    else:
        fallback = "Groq chat unreachable" if kind == "chat" else "Groq TTS unreachable"
        msg = _short_error(result, fallback)
        _set_status(msg, "err")
        print("chat_groq%s:" % ("" if kind == "chat" else " speak"), msg)
    _set_send_enabled(True)
    _busy = False


def _resume_after_generation():
    global _generation_paused
    if not _generation_paused:
        return
    inst = display_driver.event_loop.current_instance()
    if inst is not None:
        inst.enable()
    _generation_paused = False


def _complete_turn(text, voice):
    try:
        reply = _chat_completion(text)
    except Exception as exc:
        _post_ui(_turn_finished, ("chat", exc))
        return
    _post_ui(_chat_reply_ready, (reply, voice))


def send(text=None):
    """Paint a chat turn, then run network/audio work off the LVGL thread."""
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
    # Let LVGL finish painting and animating the chat log before Groq chat begins.
    _settle_ui()
    _set_status("Thinking (%s)..." % CHAT_MODEL, "accent")
    voice = GroqTTS.voice_from_label(_dd_selected_text(_voice_dd, _voice_labels))
    import _thread

    try:
        _thread.stack_size(32768)
    except (AttributeError, ValueError):
        pass
    _thread.start_new_thread(_complete_turn, (text, voice))


def _stt_status(value):
    text, tone = value
    _set_status(text, tone, refresh=False)


def _stt_listening_started(ready):
    _set_status("Listening... release BOOT to send", "accent", refresh=True)
    ready[0] = True


def _post_ui(function, value):
    """Queue worker-thread results for the runtime/LVGL owner thread."""
    _ui_jobs.append((function, value))


def _drain_ui_jobs(_timer=None):
    while _ui_jobs:
        function, value = _ui_jobs.pop(0)
        function(value)


def _stt_finished(value):
    global _listening
    _listening = False
    if isinstance(value, Exception):
        msg = _short_error(value, "Groq STT unreachable")
        _set_status(msg, "err")
        print("chat_groq listen:", msg)
        return
    if _input_ta is not None:
        _input_ta.set_text(value)
    send(value)


def _capture_and_transcribe(pressed):
    try:
        recording = _stt_client.record(bc.audio_in, while_pressed=pressed, max_ms=30000)
        if not recording.pcm:
            raise ValueError("No audio captured")
        _post_ui(_stt_status, ("Transcribing...", "accent"))
        result = _stt_client.transcribe(recording, language="en")
        _post_ui(_stt_finished, result.text)
    except Exception as exc:
        _post_ui(_stt_finished, exc)


def _start_desktop_ptt(pressed):
    global _listening
    if _busy or _listening:
        return
    import _thread

    _listening = True
    # This callback runs inside LVGL's indev read.  Forcing task_handler here
    # would recursively re-enter the same input callback.
    _set_status("Listening... release Left Ctrl to send", "accent", refresh=False)
    _thread.start_new_thread(_capture_and_transcribe, (pressed,))


def _install_push_to_talk():
    """Left Ctrl on desktop; active-low BOOT keypad key on microcontrollers."""
    import sys

    embedded = sys.implementation.name in ("micropython", "circuitpython") and sys.platform not in (
        "linux", "darwin", "win32", "unix", "webassembly", "emscripten"
    )
    from eventsys.keys import Keys

    if embedded:
        from time import sleep_ms as thread_sleep_ms

        pressed = lambda: Keys.K_LCTRL in bc.keypad.read()

        def monitor_boot():
            global _listening
            was_pressed = pressed()
            while True:
                down = pressed()
                if down and not was_pressed and not _busy and not _listening:
                    _listening = True
                    painted = [False]
                    _post_ui(_stt_listening_started, painted)
                    # Do not let the blocking I2S read monopolize the VM until
                    # the owner thread has committed the Listening frame.
                    while not painted[0] and pressed():
                        thread_sleep_ms(5)
                    _capture_and_transcribe(pressed)
                was_pressed = down
                thread_sleep_ms(10)

        import _thread

        # MicroPython may service pending soft-timer callbacks on whichever
        # Python thread currently owns the VM.  The ESP32 default worker stack
        # (~5 KiB) is too small for an LVGL task-handler pass, so size this
        # persistent monitor for both audio/STT and incidental LVGL work.
        try:
            _thread.stack_size(32768)
        except (AttributeError, ValueError):
            pass
        thread_id = _thread.start_new_thread(monitor_boot, ())
        return (bc.keypad, thread_id)

    held = [False]

    def on_key(event, *_unused):
        if event is None:
            return
        if event.key != Keys.K_LCTRL:
            return
        held[0] = event.type == bc.runtime.events.KEYDOWN
        if held[0]:
            _start_desktop_ptt(lambda: held[0])

    import eventsys

    for driver in getattr(display_driver, "_drivers", ()):
        for virtual in getattr(driver, "virtual_devices", ()):
            for device in getattr(virtual, "devices", ()):
                if device.type == eventsys.KEYPAD:
                    device.subscribe(on_key)
                    return (held, device)
    raise RuntimeError("desktop push-to-talk keypad device not found")


def _input_ready(_event):
    """Submit from a hardware or on-screen keyboard's Enter/Ready key."""
    send()


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
    dd.set_size(box_w, box_h)
    lst = dd.get_list() if hasattr(dd, "get_list") else None
    if lst is None:
        return
    lst.set_style_text_font(font, 0)
    pad_row = max(8, points // 2)
    if hasattr(lst, "set_style_pad_row"):
        lst.set_style_pad_row(pad_row, 0)
    if hasattr(lst, "set_style_text_line_space"):
        lst.set_style_text_line_space(pad_row // 2, 0)
    if hasattr(lst, "set_style_pad_ver"):
        lst.set_style_pad_ver(pad_row // 2, 0)
    if hasattr(lst, "set_style_max_height"):
        lst.set_style_max_height(box_h * 8, 0)


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
    _chat_pt = max(24, unit // 18)
    ctrl_pt = max(32, unit // 18)
    row_h = max(40, ctrl_pt + _pad)
    input_h = max(_body_pt * 3, unit // 9)
    btn_h = max(44, _body_pt * 2 + _pad // 2)
    btn_w = max(100, min(w // 3, _body_pt * 8))
    _radius = max(8, unit // 48)
    _bubble_w = max(160, w - 3 * _pad)

    _style_screen(scr)

    y = _pad
    title = lv.label(scr)
    title.set_text("Groq Chat")
    title.set_style_text_color(_color(_C_TEXT), 0)
    _set_scaled_font(title, title_pt)
    title.align(lv.ALIGN.TOP_LEFT, _pad, y)
    y += title_pt + _pad // 3

    _status = lv.label(scr)
    _status.set_text("Ask a question - Llama answers, Orpheus speaks")
    _status.set_width(w - 2 * _pad)
    _status.set_long_mode(lv.label.LONG_MODE.WRAP)
    _status.set_style_text_color(_color(_C_MUTED), 0)
    _set_scaled_font(_status, max(12, _body_pt - 2))
    _status.align(lv.ALIGN.TOP_LEFT, _pad, y)
    y += _body_pt + _pad // 2

    _voice_labels = [GroqTTS.voice_label(n, d) for n, d in GroqTTS.voices()]
    default_voice = GroqTTS.voice_label(_provider.voice)
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
    ready_event = getattr(lv.EVENT, "READY", None)
    if ready_event is not None:
        _input_ta.add_event_cb(_input_ready, ready_event, None)
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
        "Hi - ask me anything. Groq Llama answers, then Groq Orpheus reads it aloud.",
        refresh=False,
    )
finally:
    if _inst is not None:
        _inst.enable()

_refresh_ui()
_ui_job_subscription = bc.runtime.on_tick(_drain_ui_jobs, period=10)
_ptt_control = _install_push_to_talk()
print("chat_groq: ready - chat=%s speak=Groq Orpheus; hold Left Ctrl/BOOT to talk" % CHAT_MODEL)
# Returns immediately on an interactive REPL with machine.Timer / signals;
# blocks when launched as a named script (e.g. main.py boot).
display_driver.runtime.run_forever()
