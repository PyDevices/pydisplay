# SPDX-FileCopyrightText: 2021 Amir Gonnen
# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Linux librt Timer (``timer_create`` / ``timer_settime``).

Uses ctypes on CPython and ffi/uctypes on MicroPython unix.  Timer signals are
delivered to the thread that created the timer (the main thread), so callbacks
run without application-side servicing.
"""

import sys

if sys.platform != "linux":
    raise ImportError("librt timer backend requires Linux")

from .._core import _TimerCore

# librt fires timer callbacks via an RT signal on the main thread, so they run
# during a plain sleep without any application-side pumping.
_uses_signals = True

_USE_CTYPES = sys.implementation.name == "cpython"
_CLOCK_MONOTONIC = 1
_SIGEV_THREAD_ID = 4
_SYS_gettid = 186
_DEFAULT_TIMER_IDS = list(range(0xF, -1, -1))
_ALLOCATED_DEFAULT_IDS = set()


def _alloc_default_id():
    for timer_id in _DEFAULT_TIMER_IDS:
        if timer_id not in _ALLOCATED_DEFAULT_IDS:
            _ALLOCATED_DEFAULT_IDS.add(timer_id)
            return timer_id
    raise RuntimeError("no librt timer ids available")


def _free_default_id(timer_id):
    _ALLOCATED_DEFAULT_IDS.discard(timer_id)


def _period_parts(period_ms):
    total_ns = period_ms * 1_000_000
    return total_ns // 1_000_000_000, total_ns % 1_000_000_000


def _apply_period(spec, period_sec, period_ns, periodic):
    spec.it_value.tv_sec = period_sec
    spec.it_value.tv_nsec = period_ns
    if periodic:
        spec.it_interval.tv_sec = period_sec
        spec.it_interval.tv_nsec = period_ns


def _apply_sigevent(sev, signo):
    sev.sigev_notify = _SIGEV_THREAD_ID
    sev.sigev_signo = signo
    sev.sigev_notify_thread_id = _gettid()


if _USE_CTYPES:
    import ctypes
    import signal

    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    try:
        librt = ctypes.CDLL("librt.so.1", use_errno=True)
    except OSError:
        librt = libc

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

    def _librt_error(name, ret):
        if ret != 0:
            raise RuntimeError(f"{name} failed (errno={ctypes.get_errno()})")

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

else:
    import array
    import os

    import ffi
    import uctypes

    libc = ffi.open("libc.so.6")
    try:
        librt = ffi.open("librt.so")
    except OSError:
        librt = libc

    _timer_create_ = librt.func("i", "timer_create", "ipp")
    _timer_delete_ = librt.func("i", "timer_delete", "P")
    _timer_settime_ = librt.func("i", "timer_settime", "PiPp")
    _sigaction_ = libc.func("i", "sigaction", "iPp")

    _sigaction_t = {
        "sa_handler": (0 | uctypes.UINT64),
        "sa_mask": (8 | uctypes.ARRAY, 16 | uctypes.UINT64),
        "sa_flags": (136 | uctypes.INT32),
        "sa_restorer": (144 | uctypes.PTR, uctypes.UINT8),
    }
    _sigval_t = {
        "sival_int": 0 | uctypes.INT32,
        "sival_ptr": (0 | uctypes.PTR, uctypes.UINT8),
    }
    _sigevent_t = {
        "sigev_value": (0, _sigval_t),
        "sigev_signo": uctypes.sizeof(_sigval_t) | uctypes.INT32,
        "sigev_notify": (uctypes.sizeof(_sigval_t) + 4) | uctypes.INT32,
        "sigev_notify_thread_id": (uctypes.sizeof(_sigval_t) + 8) | uctypes.INT32,
    }
    _timespec_t = {
        "tv_sec": 0 | uctypes.INT32,
        "tv_nsec": 8 | uctypes.INT64,
    }
    _itimerspec_t = {
        "it_interval": (0, _timespec_t),
        "it_value": (16, _timespec_t),
    }

    _SIGRTMIN = libc.func("i", "__libc_current_sigrtmin", "")()

    try:
        _gettid = libc.func("i", "gettid", "")
    except OSError:
        _syscall = libc.func("l", "syscall", "l")

        def _gettid():
            return _syscall(_SYS_gettid)

    def _uctypes_struct(desc):
        buf = bytearray(uctypes.sizeof(desc))
        return uctypes.struct(uctypes.addressof(buf), desc, uctypes.NATIVE)

    def _librt_error(name, ret):
        if ret != 0:
            raise RuntimeError(f"{name} failed (errno={os.errno()})")


# --- shared timer + signal helpers (ctypes-style flow) ----------------


def _timer_create(sig_id):
    signo = _SIGRTMIN + sig_id
    if _USE_CTYPES:
        sev = _sigevent()
        _apply_sigevent(sev, signo)
        timerid = ctypes.c_void_p()
        _librt_error(
            "timer_create",
            librt.timer_create(_CLOCK_MONOTONIC, ctypes.byref(sev), ctypes.byref(timerid)),
        )
        return timerid

    sev = _uctypes_struct(_sigevent_t)
    _apply_sigevent(sev, signo)
    timerid = array.array("P", [0])
    _librt_error("timer_create", _timer_create_(_CLOCK_MONOTONIC, sev, timerid))
    return timerid[0]


def _timer_settime(tid, period_ms, periodic):
    period_sec, period_ns = _period_parts(period_ms)
    spec = _itimerspec() if _USE_CTYPES else _uctypes_struct(_itimerspec_t)
    _apply_period(spec, period_sec, period_ns, periodic)
    if _USE_CTYPES:
        _librt_error("timer_settime", librt.timer_settime(tid, 0, ctypes.byref(spec), None))
    else:
        old = _uctypes_struct(_itimerspec_t)
        _librt_error("timer_settime", _timer_settime_(tid, 0, spec, old))


def _timer_disarm(tid):
    _timer_settime(tid, 0, False)


def _timer_delete(tid):
    if _USE_CTYPES:
        _librt_error("timer_delete", librt.timer_delete(tid))
    else:
        _librt_error("timer_delete", _timer_delete_(tid))


def _install_signal(signum, handler):
    if _USE_CTYPES:
        signal.signal(signum, handler)
        return handler

    sa = _uctypes_struct(_sigaction_t)
    sa_old = _uctypes_struct(_sigaction_t)
    cb = ffi.callback("v", handler, "i", lock=True)
    sa.sa_handler = cb.cfun()
    _librt_error("sigaction", _sigaction_(signum, sa, sa_old))
    return cb


def _remove_signal(signum):
    if _USE_CTYPES:
        signal.signal(signum, signal.SIG_IGN)
        return

    sa = _uctypes_struct(_sigaction_t)
    sa_old = _uctypes_struct(_sigaction_t)
    # SIG_IGN — absorb any pending RT signal after timer_delete (not SIG_DFL).
    sa.sa_handler = 1
    _sigaction_(signum, sa, sa_old)


class Timer(_TimerCore):
    """Linux librt Timer (timer_create)."""

    def _arm(self):
        self._allocated_default_id = self.id == -1
        self.id = _alloc_default_id() if self._allocated_default_id else self.id
        signum = _SIGRTMIN + self.id

        def _py_handler(_signum, _frame=None):
            self._deliver()

        self._py_handler = _py_handler
        self._signal_ref = _install_signal(signum, _py_handler)
        self._timer = _timer_create(self.id)
        _timer_settime(self._timer, self._period_ms, self._mode == Timer.PERIODIC)

    def _disarm(self):
        signum = _SIGRTMIN + (self.id if self.id != -1 else 0xF)
        if self._timer is not None:
            _timer_disarm(self._timer)
            _timer_delete(self._timer)
            self._timer = None
        _remove_signal(signum)
        if getattr(self, "_allocated_default_id", False):
            _free_default_id(self.id)
            self.id = -1
            self._allocated_default_id = False
        self._py_handler = None
        self._signal_ref = None
