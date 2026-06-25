# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Prove ``multimer`` and ``eventsys`` are standalone with respect to pydisplay.

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

_MULTIMER_CHILD = textwrap.dedent(
    """
    import sys

    import multimer
    from multimer import (
        Timer,
        get_timer,
        run_queued,
        schedule,
        sleep_ms,
        ticks_add,
        ticks_diff,
        ticks_less,
        ticks_ms,
    )
    import multimer.aio  # opt-in asyncio backend must also be standalone

    forbidden = [m for m in {siblings!r} if m in sys.modules]
    assert not forbidden, "multimer pulled in pydisplay modules: %r" % forbidden

    assert ticks_ms() >= 0
    if Timer is not None:
        hits = []
        t = get_timer(lambda tmr: hits.append(1), period=10, warn=False)
        import time
        end = time.time() + 0.2
        while time.time() < end:
            run_queued()
            time.sleep(0.005)
        run_queued()
        t.deinit()
        assert hits, "standalone timer never fired"

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
            # The child sees ONLY the temp dir (plus the stdlib) — no src/lib
            # and no src/add_ons, so the rest of pydisplay is unreachable.
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
