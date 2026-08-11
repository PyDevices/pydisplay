# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Prove pydisplay packages are standalone with respect to each other.

Each test copies *only* one package into a temporary directory and imports it
in a fresh subprocess whose path contains nothing else from the repository. If
a package secretly depended on other pydisplay modules, the import would fail
or those modules would appear in ``sys.modules``. ``eventsys`` and ``displaysys``
also receive shared ``events.py`` / ``keys.py`` (not pydisplay packages).
"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import _env

_MULTIMER_SIBLINGS = ("displaysys", "eventsys", "pygraphics", "palettes")
_EVENTSYS_SIBLINGS = ("displaysys", "pygraphics", "multimer", "palettes")
_DISPLAYSYS_SIBLINGS = ("eventsys", "pygraphics", "multimer", "palettes")

_MULTIMER_CHILD = textwrap.dedent(
    """
    import sys

    import time

    import multimer
    from multimer import (
        AsyncTimer,
        Timer,
        schedule,
        sleep_ms,
        ticks_add,
        ticks_diff,
        ticks_less,
        ticks_ms,
    )

    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "multimer pulled in pydisplay modules: %r" % forbidden

    assert ticks_ms() >= 0
    seen = []
    schedule(lambda x: seen.append(x), 1)
    assert seen == [1], seen

    hits = []
    t = Timer(-1)
    t.init(period=50, callback=lambda tim: hits.append(tim))
    deadline = time.monotonic() + 0.35
    while time.monotonic() < deadline:
        sleep_ms(10)
    t.deinit()
    assert hits, "standalone timer never fired"
    assert AsyncTimer is not None, "AsyncTimer should be available on CPython"

    print("STANDALONE_OK")
    """
).format(siblings=list(_MULTIMER_SIBLINGS))

_EVENTSYS_CHILD = textwrap.dedent(
    """
    import sys

    import events
    import eventsys
    import keys
    from eventsys import KeypadDevice, Runtime, types

    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "eventsys pulled in pydisplay modules: %r" % forbidden
    assert "micropython" not in sys.modules, "eventsys requires the micropython shim"

    # Exercise a real flow: a keypad device feeding a runtime.
    runtime = Runtime()
    presses = [set([65]), set()]
    kp = KeypadDevice(read=lambda: presses.pop(0) if presses else set())
    runtime.register(kp)

    seen = []
    runtime.on_device(types.KEYPAD, seen.append)

    down = runtime.poll()
    assert down and down[0].type == events.KEYDOWN, down
    up = runtime.poll()
    assert up and up[0].type == events.KEYUP, up
    assert len(seen) == 2, seen

    assert keys.keyname(keys.K_a) == "A"

    print("STANDALONE_OK")
    """
).format(siblings=list(_EVENTSYS_SIBLINGS))


_DISPLAYSYS_CHILD = textwrap.dedent(
    """
    import sys

    import displaysys
    import events
    import keys
    from displaysys import (
        alloc_buffer,
        color332,
        color565,
        color565_swapped,
        color_rgb,
    )
    from displaysys._domkeys import key_to_keycode
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
    assert "eventsys" not in sys.modules, "displaysys imported eventsys"
    assert events.QUIT == 0x100
    assert keys.K_q
    assert key_to_keycode("BrowserBack", 0) == keys.K_AC_BACK

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
            shutil.copyfile(_env.EVENTS_PY, os.path.join(tmp, "events.py"))
            shutil.copyfile(_env.KEYS_PY, os.path.join(tmp, "keys.py"))

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

    def test_displaysys_imports_and_runs_in_isolation(self):
        tmp = tempfile.mkdtemp(prefix="displaysys_standalone_")
        try:
            shutil.copytree(_env.DISPLAYSYS_DIR, os.path.join(tmp, "displaysys"))
            shutil.copyfile(_env.EVENTS_PY, os.path.join(tmp, "events.py"))
            shutil.copyfile(_env.KEYS_PY, os.path.join(tmp, "keys.py"))

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
