# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PGDisplay frame recording via displaysys."""

import os
import tempfile
import unittest

import _env  # noqa: F401
from _support import quiet

from displaysys import FFmpegFrameRecorder


class TestFrameRecorderBase(unittest.TestCase):
    def test_fbdisplay_rejects_frame_recorder(self):
        with quiet():
            from _support import make_fbdisplay

            d, _ = make_fbdisplay(8, 4)
        with self.assertRaises(NotImplementedError):
            d.open_frame_recorder("/tmp/out.mp4")


class TestPGDisplayFrameRecorder(unittest.TestCase):
    def setUp(self):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    def test_records_logical_buffer_on_show(self):
        from displaysys.pgdisplay import PGDisplay

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "clip.mp4")
            with quiet():
                d = PGDisplay(32, 24, scale=1, title="rec-test")
            d.open_frame_recorder(out, fps=6)
            d.fill(0xFFFF)
            d.show()
            d.fill(0xF800)
            d.show()
            self.assertTrue(d.frame_recording)
            d.close_frame_recorder()
            self.assertFalse(d.frame_recording)
            self.assertTrue(os.path.getsize(out) > 0)
            d.deinit()

    def test_open_from_env(self):
        from displaysys.pgdisplay import PGDisplay

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "env.mp4")
            os.environ["PYDISPLAY_VIDEO"] = out
            os.environ["PYDISPLAY_VIDEO_FPS"] = "8"
            try:
                with quiet():
                    d = PGDisplay(16, 16, scale=1, title="env-rec")
                recorder = d.open_frame_recorder_from_env()
                self.assertIsNotNone(recorder)
                d.fill(0x07E0)
                d.show()
                d.close_frame_recorder()
                self.assertTrue(os.path.getsize(out) > 0)
                d.deinit()
            finally:
                os.environ.pop("PYDISPLAY_VIDEO", None)
                os.environ.pop("PYDISPLAY_VIDEO_FPS", None)


class TestFFmpegFrameRecorder(unittest.TestCase):
    def test_write_rejects_bad_frame_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "bad.mp4")
            rec = FFmpegFrameRecorder(out, 4, 4, fps=6)
            with self.assertRaises(ValueError):
                rec.write(b"\x00" * 10)
            rec.close()


if __name__ == "__main__":
    unittest.main()
