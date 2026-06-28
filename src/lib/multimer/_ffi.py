# SPDX-FileCopyrightText: 2021 Amir Gonnen
# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""POSIX librt Timer for MicroPython unix (ffi + uctypes)."""

# Based on timer.py from micropython-lib
# (https://github.com/micropython/micropython-lib/blob/master/unix-ffi/machine/machine/timer.py)

import array
import os

import ffi
import uctypes

from ._timerbase import _TimerBase

# FFI libraries

libc = ffi.open("libc.so.6")
try:
    librt = ffi.open("librt.so")
except OSError:
    librt = libc


# C constants

CLOCK_REALTIME = 0
CLOCK_MONOTONIC = 1
SIGEV_SIGNAL = 0
SIGEV_THREAD_ID = 4

# C structs

sigaction_t = {
    "sa_handler": (0 | uctypes.UINT64),
    "sa_mask": (8 | uctypes.ARRAY, 16 | uctypes.UINT64),
    "sa_flags": (136 | uctypes.INT32),
    "sa_restorer": (144 | uctypes.PTR, uctypes.UINT8),
}

sigval_t = {
    "sival_int": 0 | uctypes.INT32,
    "sival_ptr": (0 | uctypes.PTR, uctypes.UINT8),
}

sigevent_t = {
    "sigev_value": (0, sigval_t),
    "sigev_signo": uctypes.sizeof(sigval_t) | uctypes.INT32,
    "sigev_notify": (uctypes.sizeof(sigval_t) + 4) | uctypes.INT32,
    "sigev_notify_thread_id": (uctypes.sizeof(sigval_t) + 8) | uctypes.INT32,
}

timespec_t = {
    "tv_sec": 0 | uctypes.INT32,
    "tv_nsec": 8 | uctypes.INT64,
}

itimerspec_t = {
    "it_interval": (0, timespec_t),
    "it_value": (16, timespec_t),
}

# C functions

__libc_current_sigrtmin = libc.func("i", "__libc_current_sigrtmin", "")
SIGRTMIN = __libc_current_sigrtmin()

timer_create_ = librt.func("i", "timer_create", "ipp")
timer_delete_ = librt.func("i", "timer_delete", "i")
timer_settime_ = librt.func("i", "timer_settime", "PiPp")

sigaction_ = libc.func("i", "sigaction", "iPp")

try:
    gettid_ = libc.func("i", "gettid", "")
except OSError:
    _syscall = libc.func("l", "syscall", "l")  # SYS_gettid = 186 on x86_64

    def gettid_():
        return _syscall(186)

# Create a new C struct


def new(sdesc):
    buf = bytearray(uctypes.sizeof(sdesc))
    s = uctypes.struct(uctypes.addressof(buf), sdesc, uctypes.NATIVE)
    return s


# Posix Signal handling


def sigaction(signum, handler, flags=0):
    sa = new(sigaction_t)
    sa_old = new(sigaction_t)
    cb = ffi.callback("v", handler, "i", lock=True)
    sa.sa_handler = cb.cfun()
    sa.sa_flags = flags
    r = sigaction_(signum, sa, sa_old)
    if r != 0:
        raise RuntimeError("sigaction_ error: %d (errno = %d)" % (r, os.errno()))
    return cb  # sa_old.sa_handler


# Posix Timer handling


def timer_create(sig_id):
    sev = new(sigevent_t)
    # print(sev)
    sev.sigev_notify = SIGEV_THREAD_ID
    sev.sigev_signo = SIGRTMIN + sig_id
    sev.sigev_notify_thread_id = gettid_()
    timerid = array.array("P", [0])
    r = timer_create_(CLOCK_MONOTONIC, sev, timerid)
    if r != 0:
        raise RuntimeError("timer_create_ error: %d (errno = %d)" % (r, os.errno()))
    # print("timerid", hex(timerid[0]))
    return timerid[0]


def timer_delete(tid):
    r = timer_delete_(tid)
    if r != 0:
        raise RuntimeError("timer_delete_ error: %d (errno = %d)" % (r, os.errno()))


def timer_settime(tid, period_ms, periodic):
    period_ns = (period_ms * 1000000) % 1000000000
    period_sec = (period_ms * 1000000) // 1000000000

    new_val = new(itimerspec_t)
    new_val.it_value.tv_sec = period_sec
    new_val.it_value.tv_nsec = period_ns
    if periodic:
        new_val.it_interval.tv_sec = period_sec
        new_val.it_interval.tv_nsec = period_ns
    # print("new_val:", bytes(new_val))
    old_val = new(itimerspec_t)
    # print(new_val, old_val)
    r = timer_settime_(tid, 0, new_val, old_val)
    if r != 0:
        raise RuntimeError("timer_settime_ error: %d (errno = %d)" % (r, os.errno()))
    # print("old_val:", bytes(old_val))


# Timer class


class Timer(_TimerBase):
    """POSIX librt Timer via uctypes (MicroPython unix)."""

    BACKEND = "posix_ffi"
    NEEDS_PUMP = False

    def _start(self):
        self.id = (
            self.id if self.id != -1 else 0xF
        )  # id must be non-negative, so we use 0xF as a default
        self._timer = timer_create(self.id)
        timer_settime(self._timer, self._interval, self._mode == Timer.PERIODIC)
        self._handler_ref = self._handler
        self._action = sigaction(SIGRTMIN + self.id, self._handler_ref)

    def _stop(self):
        # timer_settime(self._timer, 0, False)
        timer_delete(self._timer)
        self._timer = None
        self._action = None
        self._handler_ref = None
