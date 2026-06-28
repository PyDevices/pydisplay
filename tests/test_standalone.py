# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Prove pydisplay packages are standalone with respect to each other.

Each test copies *only* one package into a temporary directory and imports it
in a fresh subprocess whose path contains nothing else from the repository. If
a package secretly depended on other pydisplay modules, the import would fail
or those modules would appear in ``sys.modules``.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import _env

_MULTIMER_SIBLINGS = ("displaysys", "eventsys", "graphics", "pdwidgets", "palettes")
_EVENTSYS_SIBLINGS = ("displaysys", "graphics", "multimer", "pdwidgets", "palettes")
_GRAPHICS_SIBLINGS = ("displaysys", "eventsys", "multimer", "pdwidgets", "palettes")
_DISPLAYSYS_SIBLINGS = ("eventsys", "graphics", "multimer", "pdwidgets", "palettes")

_MULTIMER_CHILD = textwrap.dedent(
    """
    import sys

    import multimer
    from multimer import (
        Timer,
        periodic,
        pump,
        schedule,
        sleep_ms,
        ticks_add,
        ticks_diff,
        ticks_less,
        ticks_ms,
        AsyncTimer,
    )

    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "multimer pulled in pydisplay modules: %r" % forbidden

    assert ticks_ms() >= 0
    hits = []
    t = periodic(lambda tmr: hits.append(1), period=10)
    import time
    end = time.time() + 0.2
    while time.time() < end:
        pump()
        time.sleep(0.005)
    pump()
    t.deinit()
    assert hits, "standalone timer never fired"
    assert AsyncTimer is not None, "AsyncTimer should be available on CPython"

    print("STANDALONE_OK")
    """
).format(siblings=list(_MULTIMER_SIBLINGS))

_EVENTSYS_CHILD = textwrap.dedent(
    """
    import sys

    import eventsys
    from eventsys import events
    from eventsys import devices
    from eventsys.devices import Broker, KeypadDevice, types
    from eventsys.keys import Keys

    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "eventsys pulled in pydisplay modules: %r" % forbidden
    assert "micropython" not in sys.modules, "eventsys requires the micropython shim"

    # Exercise a real flow: a keypad device feeding a broker.
    broker = Broker()
    presses = [set([65]), set()]
    kp = KeypadDevice(read=lambda: presses.pop(0) if presses else set())
    broker.register_device(kp)

    seen = []
    broker.subscribe(seen.append, device_types=[types.KEYPAD])

    down = broker.poll()
    assert down and down[0].type == events.KEYDOWN, down
    up = broker.poll()
    assert up and up[0].type == events.KEYUP, up
    assert len(seen) == 2, seen

    assert Keys.keyname(Keys.K_a) == "A"

    print("STANDALONE_OK")
    """
).format(siblings=list(_EVENTSYS_SIBLINGS))

_GRAPHICS_CHILD = textwrap.dedent(
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
).format(siblings=list(_GRAPHICS_SIBLINGS))

_DISPLAYSYS_CHILD = textwrap.dedent(
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
    from displaysys.fbdisplay import FBDisplay


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

    assert "multimer" not in sys.modules, "displaysys imported multimer unexpectedly"

    print("STANDALONE_OK")
    """
).format(siblings=list(_DISPLAYSYS_SIBLINGS))


class TestStandalone(unittest.TestCase):
    def test_multimer_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="multimer_standalone_")
        try:
            shutil.copytree(_env.MULTIMER_DIR, os.path.join(tmp, "multimer"))

            env = dict(os.environ)
            env["PYTHONPATH"] = tmp

            proc = subprocess.run(
                [sys.executable, "-c", _MULTIMER_CHILD],
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

    def test_eventsys_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="eventsys_standalone_")
        try:
            shutil.copytree(_env.EVENTSYS_DIR, os.path.join(tmp, "eventsys"))

            env = dict(os.environ)
            env["PYTHONPATH"] = tmp

            proc = subprocess.run(
                [sys.executable, "-c", _EVENTSYS_CHILD],
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

    def test_graphics_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="graphics_standalone_")
        try:
            shutil.copytree(_env.GRAPHICS_DIR, os.path.join(tmp, "graphics"))

            env = dict(os.environ)
            env["PYTHONPATH"] = tmp

            proc = subprocess.run(
                [sys.executable, "-c", _GRAPHICS_CHILD],
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

    def test_displaysys_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="displaysys_standalone_")
        try:
            shutil.copytree(_env.DISPLAYSYS_DIR, os.path.join(tmp, "displaysys"))

            env = dict(os.environ)
            env["PYTHONPATH"] = tmp

            proc = subprocess.run(
                [sys.executable, "-c", _DISPLAYSYS_CHILD],
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
