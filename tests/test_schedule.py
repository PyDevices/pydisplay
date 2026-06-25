# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``multimer.schedule`` / ``multimer.run_queued``."""

import threading
import unittest

import _env  # noqa: F401

import multimer
from multimer import run_queued, schedule


class TestSchedule(unittest.TestCase):
    def setUp(self):
        # Drain anything left over from a previous test so the shared module
        # queue starts empty.
        run_queued()

    def tearDown(self):
        run_queued()

    def test_requires_run_queued_flag_is_true_on_cpython(self):
        # CPython may post callbacks from worker threads, so the module-level
        # flag is true.
        self.assertTrue(multimer.REQUIRES_RUN_QUEUED)

    def test_main_thread_runs_callback_immediately(self):
        calls = []
        schedule(calls.append, "now")
        # No run_queued() needed when scheduling from the main thread.
        self.assertEqual(calls, ["now"])

    def test_worker_thread_defers_until_run_queued(self):
        calls = []
        main_ident = threading.current_thread().ident
        ran_on = []

        def cb(arg):
            calls.append(arg)
            ran_on.append(threading.current_thread().ident)

        def worker():
            schedule(cb, "later")

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        # Callback was queued, not run on the worker thread.
        self.assertEqual(calls, [])

        run_queued()
        self.assertEqual(calls, ["later"])
        # Drained on the main thread.
        self.assertEqual(ran_on, [main_ident])

    def test_run_queued_respects_max_items(self):
        calls = []

        def worker():
            for i in range(4):
                schedule(calls.append, i)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        run_queued(max_items=2)
        self.assertEqual(calls, [0, 1])
        run_queued()
        self.assertEqual(calls, [0, 1, 2, 3])


if __name__ == "__main__":
    unittest.main()
