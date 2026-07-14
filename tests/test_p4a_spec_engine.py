# SPDX-License-Identifier: MIT
"""Unit tests for examples/p4a_spec_engine.py (comment-free buildozer.spec)."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "src" / "examples"
if str(EXAMPLES) not in sys.path:
    sys.path.insert(0, str(EXAMPLES))

from p4a_spec_engine import (  # noqa: E402
    SpecModel,
    load_defaults,
    model_to_text,
    parse_spec_text,
    write_output,
)


class P4ASpecEngineTests(unittest.TestCase):
    def test_round_trip_permissions_and_skip_update(self):
        model = SpecModel(
            {
                "app": {
                    "package.name": "demo",
                    "package.domain": "org.example",
                    "version": "1.0",
                    "requirements": "python3,sdl2",
                    "orientation": "portrait",
                    "fullscreen": "0",
                    "source.include_exts": "py",
                    "android.permissions": "INTERNET, CAMERA",
                    "android.api": "31",
                    "android.minapi": "24",
                    "android.archs": "arm64-v8a",
                    "android.skip_update": "True",
                    "android.ndk": "",
                    "android.sdk": "",
                },
                "buildozer": {"log_level": "2", "warn_on_root": "0"},
            }
        )
        text = model_to_text(model)
        self.assertNotIn("#", text)
        self.assertIn("orientation = portrait", text)
        self.assertIn("android.skip_update = True", text)
        self.assertIn("android.permissions = INTERNET, CAMERA", text)
        self.assertNotIn("android.ndk =", text)
        self.assertNotIn("android.sdk =", text)

        again = SpecModel(parse_spec_text(text))
        self.assertEqual(again.list_get("android.permissions"), ["INTERNET", "CAMERA"])
        self.assertTrue(again.bool_get("android.skip_update"))

    def test_write_output_and_load_defaults(self):
        model = load_defaults()
        self.assertEqual(model.get("orientation") or "portrait", "portrait")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "buildozer.spec"
            write_output(model, path)
            body = path.read_text(encoding="utf-8")
            self.assertTrue(body.startswith("[app]"))
            self.assertNotIn("#", body)


if __name__ == "__main__":
    unittest.main()
