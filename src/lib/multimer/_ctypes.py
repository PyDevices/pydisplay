# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
POSIX librt Timer for CPython on Linux (ctypes).

Like ``_uctypes`` on MicroPython unix: timer signals are delivered to the thread
that created the timer (the main thread), so callbacks run without
``run_scheduled()``.
"""

import signal
import sys

if sys.implementation.name != "cpython" or sys.platform != "linux":
    raise ImportError("_ctypes timer requires CPython on Linux")

import ctypes

from ._timerbase import _TimerBase

libc = ctypes.CDLL("libc.so.6", use_errno=True)
try:
    librt = ctypes.CDLL("librt.so.1", use_errno=True)
except OSError:
    librt = libc

CLOCK_MONOTONIC = 1
SIGEV_THREAD_ID = 4
_SYS_gettid = 186


class _timespec(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]


class _itimerspec(ctypes.Structure):
    _fields_ = [("it_interval", _timespec), ("it_value", _timespec)]


class _sigval(ctypes.Union):
    _fields_ = [("sival_int", ctypes.c_int), ("sival_ptr", ctypes.c_void_p)]


class _sigevent(ctypes.Structure):
    _fields_ = [
        ("sigev_value", _sigval),
        ("sigev_signo", ctypes.c_int),
        ("sigev_notify", ctypes.c_int),
        ("sigev_notify_thread_id", ctypes.c_int),
    ]


def _check(name, ret):
    if ret != 0:
        err = ctypes.get_errno()
        raise RuntimeError(f"{name} failed (errno={err})")


try:
    _gettid = libc.gettid
    _gettid.restype = ctypes.c_int
    _gettid.argtypes = []
except AttributeError:
    libc.syscall.restype = ctypes.c_long
    libc.syscall.argtypes = [ctypes.c_long]

    def _gettid():
        return libc.syscall(_SYS_gettid)


librt.timer_create.restype = ctypes.c_int
librt.timer_create.argtypes = [
    ctypes.c_int,
    ctypes.POINTER(_sigevent),
    ctypes.POINTER(ctypes.c_void_p),
]
librt.timer_delete.restype = ctypes.c_int
librt.timer_delete.argtypes = [ctypes.c_void_p]
librt.timer_settime.restype = ctypes.c_int
librt.timer_settime.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.POINTER(_itimerspec),
    ctypes.POINTER(_itimerspec),
]

_SIGRTMIN = signal.SIGRTMIN


def _timer_create(sig_id):
    sev = _sigevent()
    sev.sigev_notify = SIGEV_THREAD_ID
    sev.sigev_signo = _SIGRTMIN + sig_id
    sev.sigev_notify_thread_id = _gettid()
    timerid = ctypes.c_void_p()
    _check(
        "timer_create",
        librt.timer_create(CLOCK_MONOTONIC, ctypes.byref(sev), ctypes.byref(timerid)),
    )
    return timerid


def _timer_delete(tid):
    _check("timer_delete", librt.timer_delete(tid))


def _timer_settime(tid, period_ms, periodic):
    period_ns = (period_ms * 1_000_000) % 1_000_000_000
    period_sec = (period_ms * 1_000_000) // 1_000_000_000
    new_val = _itimerspec()
    new_val.it_value.tv_sec = period_sec
    new_val.it_value.tv_nsec = period_ns
    if periodic:
        new_val.it_interval.tv_sec = period_sec
        new_val.it_interval.tv_nsec = period_ns
    _check("timer_settime", librt.timer_settime(tid, 0, ctypes.byref(new_val), None))


class Timer(_TimerBase):
    """POSIX librt Timer via ctypes (CPython Linux)."""

    REQUIRES_RUN_SCHEDULED = False

    def _start(self):
        self.id = self.id if self.id != -1 else 0xF
        signum = _SIGRTMIN + self.id

        def _py_handler(_signum, _frame):
            self._handler(_signum)

        self._py_handler = _py_handler
        signal.signal(signum, _py_handler)
        self._timer = _timer_create(self.id)
        _timer_settime(self._timer, self._interval, self._mode == Timer.PERIODIC)

    def _stop(self):
        signum = _SIGRTMIN + (self.id if self.id != -1 else 0xF)
        if self._timer:
            zero = _itimerspec()
            librt.timer_settime(self._timer, 0, ctypes.byref(zero), None)
            _timer_delete(self._timer)
            self._timer = None
        signal.signal(signum, signal.SIG_IGN)
        self._py_handler = None
