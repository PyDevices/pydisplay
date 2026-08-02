# gallery: skip
# deps: lvgl
"""LVGL textarea → Gemini TTS → board_config.audio_out.

Needs ``tts``, a ``secrets`` module with ``GEMINI_API_KEY``, and
``board_config`` with lazy ``audio_out`` in ``DEVICES`` (hardware
``board_devices``, or the desktop default in ``lib/board_config.py``).

Voice catalog comes from ``GeminiTTS.voices()`` (no list-voices HTTP
endpoint; the module exposes the documented prebuilt catalog). Style,
pace, and accent are prompt-driven via the Style field (``instructions``).
"""

import display_driver  # noqa: F401 — wires LVGL flush + input + event_loop
import lvgl as lv
import board_config as bc

from secrets import GEMINI_API_KEY
from tts import GeminiTTS, TTSClient

DEFAULT_TEXT = "Hello from MicroPython. Google text to speech is working."
DEFAULT_STYLE = "Read clearly in a friendly, relaxed voice."

_provider = GeminiTTS(GEMINI_API_KEY)
_client = TTSClient(_provider, chunk_size=4096)
_status = None
_voice_dd = None
_style_ta = None
_text_ta = None
_voice_labels = []


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
    style = (_style_ta.get_text() if _style_ta is not None else DEFAULT_STYLE).strip()
    return {
        "voice": GeminiTTS.voice_from_label(_dd_selected_text(_voice_dd, _voice_labels)),
        "instructions": style or DEFAULT_STYLE,
    }


def _status_for_error(exc):
    """Short status line; pull retry delay out of Gemini quota errors."""
    msg = str(exc)
    lower = msg.lower()
    key = "retry in "
    i = lower.find(key)
    if i >= 0:
        num = []
        for ch in msg[i + len(key) :]:
            if ch.isdigit() or ch == ".":
                num.append(ch)
            elif num:
                break
        if num:
            try:
                secs = int(float("".join(num)))
                return "Please retry in %d seconds." % secs
            except ValueError:
                pass
    if "quota" in lower:
        return "Quota exceeded. Please retry later."
    if len(msg) > 80:
        return msg[:77] + "..."
    return msg


def speak(text=None):
    if text is None and _text_ta is not None:
        text = _text_ta.get_text()
    text = (text or "").strip()
    if not text:
        return 0
    if "audio_out" not in bc.DEVICES:
        raise RuntimeError("board_config has no audio_out in DEVICES")
    if _status is not None:
        _status.set_text("Speaking...")
        _refresh_ui()
    output = bc.audio_out
    set_vol = getattr(output, "set_volume", None)
    if set_vol is not None:
        set_vol(85)
    try:
        total = _client.speak(text, output, **_speak_options())
    except Exception as exc:
        # Never re-raise from the LVGL click handler — that stalls the UI.
        if _status is not None:
            _status.set_text(_status_for_error(exc))
            _refresh_ui()
        print("tts_lvgl:", _status_for_error(exc))
        return 0
    finally:
        output.close()
    if _status is not None:
        _status.set_text("Done (%d bytes)" % total)
        _refresh_ui()
    return total


def _add_label(parent, text, body_pt, y, w, pad):
    lbl = lv.label(parent)
    lbl.set_text(text)
    _set_font(lbl, body_pt)
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
    # Widen the open list to the full control width.
    if hasattr(lst, "set_style_max_height"):
        lst.set_style_max_height(box_h * 8, 0)


def _add_dropdown(parent, options, selected, ctrl_pt, y, w, pad, row_h):
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
    title = lv.label(form)
    title.set_text("Google TTS")
    _set_scaled_font(title, title_pt)
    title.align(lv.ALIGN.TOP_LEFT, pad, y)
    y += title_pt + pad // 2

    _status = lv.label(form)
    _status.set_text("Tap Speak to play the text")
    _status.set_width(w - 2 * pad)
    _set_scaled_font(_status, body_pt)
    _status.align(lv.ALIGN.TOP_LEFT, pad, y)
    y += body_pt + pad

    _voice_labels = [GeminiTTS.voice_label(n, d) for n, d in GeminiTTS.voices()]
    default_voice = GeminiTTS.voice_label(_provider.voice)

    _add_label(form, "Voice", body_pt, y, w, pad)
    y += label_h
    _voice_dd = _add_dropdown(form, _voice_labels, default_voice, ctrl_pt, y, w, pad, row_h)
    y += row_h + pad // 2

    _add_label(form, "Style (instructions)", body_pt, y, w, pad)
    y += label_h
    _style_ta = lv.textarea(form)
    _style_ta.set_text(DEFAULT_STYLE)
    _style_ta.set_size(w - 2 * pad, style_h)
    _set_font(_style_ta, body_pt)
    _style_ta.align(lv.ALIGN.TOP_LEFT, pad, y)
    y += style_h + pad // 2

    _add_label(form, "Text", body_pt, y, w, pad)
    y += label_h
    ta_h = max(body_pt * 5, h // 4)
    _text_ta = lv.textarea(form)
    _text_ta.set_text(DEFAULT_TEXT)
    _text_ta.set_size(w - 2 * pad, ta_h)
    _set_font(_text_ta, body_pt)
    _text_ta.align(lv.ALIGN.TOP_LEFT, pad, y)
    lv.group_focus_obj(_text_ta)
    y += ta_h + pad

    btn = lv.button(form)
    btn.set_size(btn_w, btn_h)
    btn.align(lv.ALIGN.TOP_MID, 0, y)
    lbl = lv.label(btn)
    lbl.set_text("Speak")
    _set_scaled_font(lbl, body_pt)
    lbl.center()
    btn.add_event_cb(lambda _e: speak(), lv.EVENT.CLICKED, None)
    y += btn_h + pad
    if hasattr(form, "set_style_min_height"):
        form.set_style_min_height(y, 0)
finally:
    if _inst is not None:
        _inst.enable()

_refresh_ui()
print("tts_lvgl: ready — pick voice/style, then tap Speak")
# Returns immediately on an interactive REPL with machine.Timer / signals;
# blocks when launched as a named script (e.g. main.py boot).
display_driver.runtime.run_forever()
