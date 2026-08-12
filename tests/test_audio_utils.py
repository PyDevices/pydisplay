# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Unit tests for ``lib/utils/audio.py`` (no real audio device)."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
UTILS = ROOT / "lib" / "utils"
if str(UTILS) not in sys.path:
    sys.path.insert(0, str(UTILS))

from audio import (  # noqa: E402
    AudioEngine,
    Mixer,
    midi_to_hz,
    note_to_hz,
    note_to_midi,
    register_wave,
    wave_names,
)


class _FakeFormat:
    rate = 24000
    channels = 1
    bits = 16
    frame_size = 2
    signed = True


class _FakeOut:
    def __init__(self):
        self.format = _FakeFormat()
        self.writes = []
        self.opened = False

    def open(self):
        self.opened = True
        return self

    def write(self, buf):
        self.writes.append(bytes(buf))
        return len(buf)

    def service(self):
        pass

    def close(self):
        self.opened = False


class NoteHelpersTests(unittest.TestCase):
    def test_note_parsing(self):
        self.assertEqual(note_to_midi("C4"), 60)
        self.assertEqual(note_to_midi("A4"), 69)
        self.assertEqual(note_to_midi("C#4"), 61)
        self.assertEqual(note_to_midi("Bb3"), 58)
        self.assertAlmostEqual(note_to_hz("A4"), 440.0, places=2)
        self.assertAlmostEqual(midi_to_hz(69), 440.0, places=2)


class MixerTests(unittest.TestCase):
    def test_chord_and_release(self):
        m = Mixer(24000, master=0.5)
        m.note_on("c", 261.63, wave="sine")
        m.note_on("e", 329.63, wave="sine")
        pcm = m.render(240)
        self.assertEqual(len(pcm), 480)
        self.assertTrue(any(pcm))
        m.note_off_all(immediate=True)
        self.assertEqual(m.voice_count, 0)
        silent = m.render(240)
        self.assertTrue(all(b == 0 for b in silent))

    def test_custom_wave(self):
        register_wave("one", lambda _phase: 1.0)
        self.assertIn("one", wave_names())
        m = Mixer(8000, master=1.0)
        m.note_on("v", 440, amp=1.0, wave="one", attack=1, release=1)
        pcm = m.render(16)
        # First sample may be attack; later samples near full scale.
        self.assertGreater(pcm[14] | (pcm[15] << 8), 0)


class EngineTests(unittest.TestCase):
    def test_note_and_blip(self):
        out = _FakeOut()
        eng = AudioEngine(out, chunk_ms=20)
        eng.note_on(1, "C4")
        self.assertTrue(out.opened)
        self.assertGreaterEqual(len(out.writes), 1)
        eng.blip(880, ms=40)
        eng.note_off(1, immediate=True)
        eng.close()
        self.assertFalse(out.opened)


if __name__ == "__main__":
    unittest.main()
