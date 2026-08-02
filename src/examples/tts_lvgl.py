# gallery: skip
# deps: lvgl
"""LVGL textarea → Gemini TTS → board_config.audio_out.

Needs ``tts``, a ``secrets`` module with ``GEMINI_API_KEY``, and
``board_config`` with lazy ``audio_out`` in ``DEVICES`` (hardware
``board_devices``, or the desktop default in ``lib/board_config.py``).
"""

import display_driver  # noqa: F401 — wires LVGL flush + input + event_loop
import lvgl as lv
import board_config as bc

from secrets import GEMINI_API_KEY
from tts import GeminiTTS, TTSClient

DEFAULT_TEXT = "Hello from MicroPython. Google text to speech is working."

_client = TTSClient(GeminiTTS(GEMINI_API_KEY), chunk_size=4096)
_status = None


def _refresh_ui():
    """Force a paint so UI updates show before blocking I/O (HTTP / audio)."""
    inst = display_driver.event_loop.current_instance()
    lv.screen_active().invalidate()
    try:
        lv.refr_now(lv.display_get_default())
    except TypeError:
        lv.refr_now(None)
    # Clear present cadence gate so the next show() is not deferred.
    display_driver._present_next_ok_ms = None
    if inst is not None:
        inst.task_handler()
    display_driver._present_lvgl_displays()


def speak(text):
    text = (text or "").strip()
    if not text:
        return 0
    if "audio_out" not in bc.DEVICES:
        raise RuntimeError("board_config has no audio_out in DEVICES")
    if _status is not None:
        _status.set_text("Speaking…")
        _refresh_ui()
    output = bc.audio_out
    set_vol = getattr(output, "set_volume", None)
    if set_vol is not None:
        set_vol(85)
    try:
        total = _client.speak(
            text,
            output,
            instructions="Read clearly in a friendly, relaxed voice.",
        )
    finally:
        output.close()
    if _status is not None:
        _status.set_text("Done (%d bytes)" % total)
        _refresh_ui()
    return total


# Build UI with the LVGL event loop paused (same pattern as lvgl_test.py).
_inst = display_driver.event_loop.current_instance()
if _inst is not None:
    _inst.disable()
try:
    scr = lv.screen_active()
    pad = 12
    w, h = scr.get_width(), scr.get_height()
    ta_h = max(120, h // 3)

    title = lv.label(scr)
    title.set_text("Google TTS")
    title.align(lv.ALIGN.TOP_LEFT, pad, pad)

    _status = lv.label(scr)
    _status.set_text("Tap Speak to play the text")
    _status.set_width(w - 2 * pad)
    _status.align(lv.ALIGN.TOP_LEFT, pad, pad + 28)

    ta = lv.textarea(scr)
    ta.set_text(DEFAULT_TEXT)
    ta.set_size(w - 2 * pad, ta_h)
    ta.align(lv.ALIGN.TOP_MID, 0, pad + 56)
    lv.group_focus_obj(ta)

    btn = lv.button(scr)
    btn.set_size(160, 48)
    btn.align(lv.ALIGN.TOP_MID, 0, pad + 56 + ta_h + pad)
    lbl = lv.label(btn)
    lbl.set_text("Speak")
    lbl.center()
    btn.add_event_cb(lambda _e: speak(ta.get_text()), lv.EVENT.CLICKED, None)
finally:
    if _inst is not None:
        _inst.enable()

_refresh_ui()
print("tts_lvgl: ready — type in the field, then tap Speak")
# Returns immediately on an interactive REPL with machine.Timer / signals;
# blocks when launched as a named script (e.g. main.py boot).
display_driver.runtime.run_forever()
