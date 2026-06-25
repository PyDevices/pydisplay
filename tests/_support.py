# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Helpers shared by the synchronous timer tests."""

import time

import _env  # noqa: F401

import multimer


def pump(duration_s, step_s=0.005):
    """Drive timers for ``duration_s`` seconds.

    Works across every synchronous backend:

    - threading / SDL / polling backends deliver callbacks through the schedule
      queue, which ``multimer.run_queued()`` drains here on the main thread;
    - the POSIX ``_ctypes``/``_ffi`` backends deliver callbacks on the main
      thread during ``time.sleep`` (``run_queued`` is then a harmless no-op).
    """
    end = time.monotonic() + duration_s
    while time.monotonic() < end:
        multimer.run_queued()
        time.sleep(step_s)
    multimer.run_queued()
