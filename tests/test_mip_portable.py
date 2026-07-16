"""Unit tests for add_ons/mip.py (portable host mip)."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

_ADD_ONS = Path(__file__).resolve().parents[1] / "src" / "add_ons"
if str(_ADD_ONS) not in sys.path:
    sys.path.insert(0, str(_ADD_ONS))

import mip  # noqa: E402


class MipPortableTests(unittest.TestCase):
    def test_rewrite_github(self):
        url = mip._rewrite_url("github:org/repo/path/file.py", "main")
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/org/repo/main/path/file.py",
        )

    def test_rewrite_github_default_branch_head(self):
        url = mip._rewrite_url("github:PyDevices/pydisplay/packages/x.json")
        self.assertEqual(
            url,
            "https://raw.githubusercontent.com/PyDevices/pydisplay/HEAD/packages/x.json",
        )

    def test_install_local_package_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            src = tmp_path / "pkg"
            src.mkdir()
            (src / "hello.py").write_text("x = 1\n", encoding="utf-8")
            manifest = tmp_path / "package.json"
            manifest.write_text(
                json.dumps(
                    {
                        "urls": [["hello.py", str(src / "hello.py")]],
                        "version": "0.1",
                    }
                ),
                encoding="utf-8",
            )
            dest = tmp_path / "out"
            mip.install(str(manifest), target=str(dest), mpy=False)
            self.assertTrue((dest / "hello.py").is_file())
            self.assertEqual((dest / "hello.py").read_text(encoding="utf-8"), "x = 1\n")

    def test_install_relative_urls_against_json_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pkg = tmp_path / "bundle"
            pkg.mkdir()
            (pkg / "mod.py").write_text("ok\n", encoding="utf-8")
            manifest = pkg / "package.json"
            manifest.write_text(
                json.dumps({"urls": [["mod.py", "./mod.py"]], "version": "0"}),
                encoding="utf-8",
            )
            dest = tmp_path / "target"
            mip.install(str(manifest), target=str(dest), mpy=False)
            self.assertEqual((dest / "mod.py").read_text(encoding="utf-8"), "ok\n")

    def test_default_mpy_false_on_cpython(self):
        self.assertFalse(mip._default_mpy())

    def test_github_install_uses_http(self):
        payload = json.dumps(
            {
                "urls": [
                    [
                        "gui/core/x.py",
                        "github:peterhinch/micropython-nano-gui/gui/core/x.py",
                    ]
                ],
                "version": "0.1",
            }
        ).encode()

        def fake_get(url):
            if url.endswith("package.json") or "packages/" in url:
                return payload
            if url.endswith("x.py"):
                return b"# gui\n"
            raise AssertionError("unexpected URL " + url)

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "add_ons"
            with mock.patch.object(mip, "_http_get", side_effect=fake_get):
                mip.install(
                    "github:PyDevices/pydisplay/packages/micropython-nano-gui.json",
                    target=str(dest),
                    mpy=False,
                )
            self.assertEqual(
                (dest / "gui" / "core" / "x.py").read_text(encoding="utf-8"), "# gui\n"
            )


if __name__ == "__main__":
    unittest.main()
