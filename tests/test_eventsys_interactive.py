# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for eventsys interactive-session detection."""

import contextlib
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

import _env  # noqa: F401

from eventsys._runtime import (
    _cmdline_has_batch_flag,
    _cmdline_has_dash_i,
    _is_interactive_session,
)


class TestCmdlineHasDashI(unittest.TestCase):
    def test_missing_path_false(self):
        self.assertFalse(_cmdline_has_dash_i("/no/such/cmdline"))

    def test_tokens_with_dash_i(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"micropython\0-i\0/tmp/app.py\0")
            path = f.name
        try:
            self.assertTrue(_cmdline_has_dash_i(path))
        finally:
            os.unlink(path)

    def test_tokens_without_dash_i(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"micropython\0/tmp/app.py\0")
            path = f.name
        try:
            self.assertFalse(_cmdline_has_dash_i(path))
        finally:
            os.unlink(path)


class TestCmdlineHasBatchFlag(unittest.TestCase):
    def test_missing_path_false(self):
        self.assertFalse(_cmdline_has_batch_flag("/no/such/cmdline"))

    def test_dash_m(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"micropython\0-m\0examples.roku_remote\0")
            path = f.name
        try:
            self.assertTrue(_cmdline_has_batch_flag(path))
        finally:
            os.unlink(path)

    def test_dash_c(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"micropython\0-c\0print(1)\0")
            path = f.name
        try:
            self.assertTrue(_cmdline_has_batch_flag(path))
        finally:
            os.unlink(path)

    def test_script_only(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"micropython\0/tmp/app.py\0")
            path = f.name
        try:
            self.assertFalse(_cmdline_has_batch_flag(path))
        finally:
            os.unlink(path)


class TestIsInteractiveSession(unittest.TestCase):
    def test_cpython_batch_process_false(self):
        # unittest entry has a real __main__.__file__; not a bare REPL.
        if sys.implementation.name != "cpython":
            self.skipTest("CPython only")
        self.assertFalse(_is_interactive_session())

    def test_cpython_flags_interactive(self):
        if sys.implementation.name != "cpython":
            self.skipTest("CPython only")
        flags = mock.Mock(interactive=1)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "flags", flags))
            stack.enter_context(
                mock.patch("eventsys._runtime._main_file", return_value="/tmp/app.py")
            )
            self.assertTrue(_is_interactive_session())

    def test_cpython_bare_repl_main_file_none(self):
        if sys.implementation.name != "cpython":
            self.skipTest("CPython only")
        flags = mock.Mock(interactive=0)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "flags", flags))
            stack.enter_context(mock.patch("eventsys._runtime._main_file", return_value=None))
            self.assertTrue(_is_interactive_session())

    def test_cpython_stdin_file_not_interactive(self):
        if sys.implementation.name != "cpython":
            self.skipTest("CPython only")
        flags = mock.Mock(interactive=0)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "flags", flags))
            stack.enter_context(mock.patch("eventsys._runtime._main_file", return_value="<stdin>"))
            self.assertFalse(_is_interactive_session())

    def test_micropython_cmdline_dash_i(self):
        impl = types.SimpleNamespace(name="micropython")
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "implementation", impl))
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_dash_i", return_value=True)
            )
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_batch_flag", return_value=True)
            )
            stack.enter_context(
                mock.patch("eventsys._runtime._main_file", return_value="/tmp/app.py")
            )
            self.assertTrue(_is_interactive_session())

    def test_micropython_script_no_dash_i(self):
        impl = types.SimpleNamespace(name="micropython")
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "implementation", impl))
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_dash_i", return_value=False)
            )
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_batch_flag", return_value=False)
            )
            stack.enter_context(
                mock.patch("eventsys._runtime._main_file", return_value="/tmp/app.py")
            )
            self.assertFalse(_is_interactive_session())

    def test_micropython_bare_repl(self):
        impl = types.SimpleNamespace(name="micropython")
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "implementation", impl))
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_dash_i", return_value=False)
            )
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_batch_flag", return_value=False)
            )
            stack.enter_context(mock.patch("eventsys._runtime._main_file", return_value=None))
            self.assertTrue(_is_interactive_session())

    def test_micropython_dash_m_no_main_file_blocks(self):
        """``-m pkg`` often has no ``__main__.__file__`` but must still block."""
        impl = types.SimpleNamespace(name="micropython")
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "implementation", impl))
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_dash_i", return_value=False)
            )
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_batch_flag", return_value=True)
            )
            stack.enter_context(mock.patch("eventsys._runtime._main_file", return_value=None))
            self.assertFalse(_is_interactive_session())

    def test_micropython_dash_i_with_dash_m_interactive(self):
        impl = types.SimpleNamespace(name="micropython")
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "implementation", impl))
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_dash_i", return_value=True)
            )
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_batch_flag", return_value=True)
            )
            stack.enter_context(mock.patch("eventsys._runtime._main_file", return_value=None))
            self.assertTrue(_is_interactive_session())

    def test_micropython_stdin_paste_interactive(self):
        """mpftp / raw-REPL paste keeps a REPL; ``run_forever`` should return."""
        impl = types.SimpleNamespace(name="micropython")
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "implementation", impl))
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_dash_i", return_value=False)
            )
            stack.enter_context(
                mock.patch("eventsys._runtime._cmdline_has_batch_flag", return_value=False)
            )
            stack.enter_context(mock.patch("eventsys._runtime._main_file", return_value="<stdin>"))
            self.assertTrue(_is_interactive_session())


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux subprocess/PTY probes")
class TestInteractiveSubprocess(unittest.TestCase):
    def test_cpython_dash_i_subprocess(self):
        import subprocess

        code = (
            "from eventsys._runtime import _is_interactive_session; "
            "print('I', int(_is_interactive_session()))"
        )
        env = os.environ.copy()
        # Ensure src/lib is on path like other tests
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "lib"))
        env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, "-i", "-c", code],
            input="\n",
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
            check=False,
        )
        self.assertIn("I 1", proc.stdout + proc.stderr, msg=repr((proc.stdout, proc.stderr)))

    def test_micropython_batch_and_dash_i(self):
        import subprocess

        mp = os.environ.get(
            "MICROPYTHON",
            "/home/brad/gh/pydevices/cmods/micropython/ports/unix/build-standard/micropython",
        )
        if not os.path.isfile(mp):
            self.skipTest("micropython unix binary not found")
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "lib"))
        script = os.path.join(tempfile.gettempdir(), "pd_interactive_mp_probe.py")
        with open(script, "w") as f:
            f.write(
                "import sys\n"
                f"sys.path.insert(0, {root!r})\n"
                "from eventsys._runtime import _is_interactive_session\n"
                "print('I', int(_is_interactive_session()))\n"
            )
        try:
            batch = subprocess.run(
                [mp, script], capture_output=True, text=True, timeout=10, check=False
            )
            self.assertEqual(batch.returncode, 0, msg=batch.stderr)
            self.assertIn("I 0", batch.stdout)

            dash_i = subprocess.run(
                [mp, "-i", script],
                input="\x04",
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertIn("I 1", dash_i.stdout + dash_i.stderr, msg=repr(dash_i.stdout))

            # ``-m`` must not look like a bare REPL (no __main__.__file__).
            mod_dir = tempfile.mkdtemp(prefix="pd_mp_m_")
            try:
                init = os.path.join(mod_dir, "pd_m_probe")
                os.makedirs(init)
                with open(os.path.join(init, "__init__.py"), "w") as f:
                    f.write("")
                with open(os.path.join(init, "__main__.py"), "w") as f:
                    f.write(
                        "import sys\n"
                        f"sys.path.insert(0, {root!r})\n"
                        "from eventsys._runtime import _is_interactive_session\n"
                        "print('I', int(_is_interactive_session()))\n"
                    )
                dash_m = subprocess.run(
                    [mp, "-m", "pd_m_probe"],
                    cwd=mod_dir,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(dash_m.returncode, 0, msg=dash_m.stderr)
                self.assertIn("I 0", dash_m.stdout, msg=repr(dash_m.stdout))
            finally:
                import shutil

                shutil.rmtree(mod_dir, ignore_errors=True)
        finally:
            try:
                os.unlink(script)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
