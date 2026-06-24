# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Prove ``graphics`` is standalone with respect to the rest of pydisplay.

This copies *only* the ``graphics`` package into a temporary directory and
imports it in a fresh subprocess whose path contains nothing else from the
repository. If ``graphics`` secretly depended on ``displaysys``/``eventsys``/
``multimer``/``pdwidgets``/etc., the import would fail or those modules would
appear in ``sys.modules``.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import _env

_PYDISPLAY_SIBLINGS = ("displaysys", "eventsys", "multimer", "pdwidgets", "palettes")

_CHILD = textwrap.dedent(
    """
    import sys

    import graphics
    from graphics import (
        Area,
        Draw,
        FrameBuffer,
        Font,
        RGB565,
        circle,
        rect,
        text8,
    )

    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "graphics pulled in pydisplay modules: %r" % forbidden

    fb = FrameBuffer(bytearray(16 * 16 * 2), 16, 16, RGB565)
    fb.fill(0)
    assert fb.fill_rect(1, 1, 3, 3, 0xFFFF) == Area(1, 1, 3, 3)
    assert fb.pixel(2, 2) == 0xFFFF

    draw = Draw(fb)
    draw.circle(8, 8, 3, 0x1234)
    text8(fb, "Hi", 0, 0, 0xFFFF)

    print("STANDALONE_OK")
    """
).format(siblings=list(_PYDISPLAY_SIBLINGS))


class TestStandalone(unittest.TestCase):
    def test_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="graphics_standalone_")
        try:
            shutil.copytree(_env.GRAPHICS_DIR, os.path.join(tmp, "graphics"))

            env = dict(os.environ)
            # The child sees ONLY the temp dir (plus the stdlib / site-packages)
            # — no src/lib, so the rest of pydisplay is unreachable.
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
