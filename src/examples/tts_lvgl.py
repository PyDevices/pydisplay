# gallery: skip
# deps: lvgl
"""LVGL textarea → Gemini TTS → SDL audio.

Needs ``tts``, ``sdl2audio``, ``audiodev``, and a ``secrets`` module that
provides ``GEMINI_API_KEY``.
"""

import display_driver  # noqa: F401 — wires LVGL flush + input + event_loop
import lvgl as lv

from audiodev import AudioFormat
from sdl2audio import audio_out
from secrets import GEMINI_API_KEY
from tts import GeminiTTS, TTSClient

DEFAULT_TEXT = "Hello from MicroPython. Google text to speech is working."

_client = TTSClient(GeminiTTS(GEMINI_API_KEY), chunk_size=4096)
_status = None


def speak(text):
    text = (text or "").strip()
    if not text:
        return 0
    if _status is not None:
        _status.set_text("Speaking…")
    output = audio_out(AudioFormat(24000, 1, 16), queue_ms=150)
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
    return total


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

print("tts_lvgl: ready — click the SDL window, then type in the field")
if __name__ == "__main__":
    display_driver.runtime.run_forever()
