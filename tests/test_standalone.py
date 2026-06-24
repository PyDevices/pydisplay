# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Prove ``displaysys`` is standalone with respect to the rest of pydisplay.

This copies *only* the ``displaysys`` package into a temporary directory and
imports it in a fresh subprocess whose path contains nothing else from the
repository. If ``displaysys`` secretly depended on ``eventsys``/``graphics``/
``multimer``/``pdwidgets``/etc. at import time, the import would fail or those
modules would appear in ``sys.modules``.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import _env

_PYDISPLAY_SIBLINGS = ("eventsys", "graphics", "multimer", "pdwidgets", "palettes")

_CHILD = textwrap.dedent(
    """
    import sys

    import displaysys
    from displaysys import (
        alloc_buffer,
        color332,
        color565,
        color565_swapped,
        color_rgb,
    )
    from displaysys.fbdisplay import FBDisplay  # pure-Python driver, displaysys-only


    class FakeFrameBuffer:
        def __init__(self, width, height, bpp=2):
            self.width = width
            self.height = height
            self.data = bytearray(width * height * bpp)

        def __buffer__(self, flags):
            return memoryview(self.data)

        def refresh(self):
            pass


    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "displaysys pulled in pydisplay modules: %r" % forbidden

    assert color565(255, 255, 255) == 0xFFFF
    assert color_rgb(0x0000) == (0, 0, 0)
    assert len(alloc_buffer(8)) == 8

    fb = FakeFrameBuffer(4, 2)
    d = FBDisplay(fb)
    d.fill(0xFFFF)
    assert bytes(fb.data) == b"\\xff\\xff" * 8, "FBDisplay.fill did not paint buffer"
    d.deinit()

    # auto_refresh is the only path that would pull in multimer; confirm it
    # stayed out of a plain import + draw.
    assert "multimer" not in sys.modules, "displaysys imported multimer unexpectedly"

    print("STANDALONE_OK")
    """
).format(siblings=list(_PYDISPLAY_SIBLINGS))


class TestStandalone(unittest.TestCase):
    def test_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="displaysys_standalone_")
        try:
            shutil.copytree(_env.DISPLAYSYS_DIR, os.path.join(tmp, "displaysys"))

            env = dict(os.environ)
            # The child sees ONLY the temp dir (plus the stdlib) — no src/lib,
            # so the rest of pydisplay is unreachable.
            env["PYTHONPATH"] = tmp

            proc = subprocess.run(
                [sys.executable, "-c", _CHILD],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                proc.returncode,
                0,
                msg=f"child failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            )
            self.assertIn("STANDALONE_OK", proc.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
