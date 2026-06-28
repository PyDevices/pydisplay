# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``multimer.schedule`` / ``multimer.pump``."""

import threading
import unittest

import _env  # noqa: F401

import multimer
from multimer import pump, schedule


class TestSchedule(unittest.TestCase):
    def setUp(self):
        pump()

    def tearDown(self):
        pump()

    def test_schedule_queue_flag_on_cpython(self):
        caps = multimer.capabilities()
        self.assertTrue(caps["schedule_queue"])

    def test_main_thread_runs_callback_immediately(self):
        calls = []
        schedule(calls.append, "now")
        self.assertEqual(calls, ["now"])

    def test_worker_thread_defers_until_pump(self):
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

        self.assertEqual(calls, [])

        pump()
        self.assertEqual(calls, ["later"])
        self.assertEqual(ran_on, [main_ident])

    def test_pump_respects_max_items(self):
        calls = []

        def worker():
            for i in range(4):
                schedule(calls.append, i)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        pump(max_items=2)
        self.assertEqual(calls, [0, 1])
        pump()
        self.assertEqual(calls, [0, 1, 2, 3])


if __name__ == "__main__":
    unittest.main()
