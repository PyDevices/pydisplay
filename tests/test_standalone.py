# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Prove eventsys is standalone with respect to the rest of pydisplay.

Copies *only* ``eventsys`` plus shared ``events.py`` / ``keys.py`` into a
temporary directory and imports it in a fresh subprocess.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import _env

_EVENTSYS_SIBLINGS = ("displaydev", "pygraphics", "multimer", "palettes")

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


class TestStandalone(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
