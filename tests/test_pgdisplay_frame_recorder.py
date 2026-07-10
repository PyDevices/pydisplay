# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""PGDisplay frame recording via displaysys."""

import importlib.util
import io
import os
import tempfile
import unittest
from unittest import mock

import _env  # noqa: F401
from _support import quiet

# pygame (pygame-ce) is only installed on Windows; unix uses SDL2. The PGDisplay
# tests below skip when pygame is unavailable. Import backends lazily so
# collection does not preload ``displaysys.pgdisplay`` into ``sys.modules``.
HAS_PYGAME = importlib.util.find_spec("pygame") is not None


def _fake_popen(cmd, stdin=None, stdout=None, stderr=None, **kwargs):
    """Stub ffmpeg: write a non-empty placeholder MP4 on ``wait()``."""
    out_path = cmd[-1]
    proc = mock.Mock()
    proc.stdin = io.BytesIO()
    proc.stderr = io.BytesIO(b"")

    def _wait():
        with open(out_path, "wb") as fh:
            fh.write(b"\x00" * 128)
        return 0

    proc.wait = _wait
    return proc


class TestFrameRecorderBase(unittest.TestCase):
    def test_fbdisplay_has_no_frame_recorder(self):
        with quiet():
            from _support import make_fbdisplay

            d, _ = make_fbdisplay(8, 4)
        self.assertFalse(hasattr(d, "open_frame_recorder"))


@unittest.skipUnless(HAS_PYGAME, "pygame (pygame-ce) required for PGDisplay tests")
class TestPGDisplayFrameRecorder(unittest.TestCase):
    def setUp(self):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        self._popen = mock.patch("subprocess.Popen", side_effect=_fake_popen)
        self._popen.start()

    def tearDown(self):
        self._popen.stop()

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


@unittest.skipUnless(HAS_PYGAME, "pygame required to import pgdisplay")
class TestFFmpegFrameRecorder(unittest.TestCase):
    def setUp(self):
        self._popen = mock.patch("subprocess.Popen", side_effect=_fake_popen)
        self._popen.start()

    def tearDown(self):
        self._popen.stop()

    def test_write_rejects_bad_frame_size(self):
        from displaysys.pgdisplay import FFmpegFrameRecorder

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "bad.mp4")
            rec = FFmpegFrameRecorder(out, 4, 4, fps=6)
            with self.assertRaises(ValueError):
                rec.write(b"\x00" * 10)
            rec.close()


if __name__ == "__main__":
    unittest.main()
