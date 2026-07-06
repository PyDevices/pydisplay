# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Windows kernel32 timer backend (waitable timer + QueueUserAPC).

Timer callbacks are queued to the thread that created the timer (the main
thread) and run during alertable waits (``SleepEx``). Host display poll or
asyncio can provide alertable waits.
"""

import sys

if sys.platform != "win32":
    raise ImportError("win32 timer backend requires win32")

import ctypes

from .._core import _TimerCore

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

INFINITE = 0xFFFFFFFF
WAIT_OBJECT_0 = 0
THREAD_SET_CONTEXT = 0x0010

_APCPROC = ctypes.WINFUNCTYPE(None, _ULONG_PTR)


class _LARGE_INTEGER(ctypes.Structure):
    _fields_ = [("QuadPart", ctypes.c_longlong)]


_main_thread_handle = None
_active = False
_registry = {}
_next_token = 1
_registry_lock = None


def _make_lock():
    import threading

    return threading.Lock()


def is_active():
    return _active


def process_apcs():
    """Process pending APCs on the main thread (non-blocking)."""
    if _main_thread_handle:
        kernel32.SleepEx(0, True)


def sleep_ex(ms):
    """Alertable sleep — timer APCs may run during the wait."""
    ms = max(ms, 0)
    kernel32.SleepEx(int(ms), True)


def _ensure_main_thread():
    global _main_thread_handle, _active, _registry_lock
    if _registry_lock is None:
        _registry_lock = _make_lock()
    if _main_thread_handle is None:
        tid = kernel32.GetCurrentThreadId()
        handle = kernel32.OpenThread(THREAD_SET_CONTEXT, False, tid)
        if not handle:
            raise OSError("OpenThread failed", ctypes.get_last_error())
        _main_thread_handle = handle
        _active = True


def _alloc_token(timer):
    global _next_token
    with _registry_lock:
        token = _next_token
        _next_token += 1
        _registry[token] = timer
    return token


def _free_token(token):
    with _registry_lock:
        _registry.pop(token, None)


@_APCPROC
def _apc_entry(param):
    timer = _registry.get(int(param))
    if timer is None or not timer._running:
        return
    timer._deliver()


def _spawn(fn):
    import threading

    threading.Thread(target=fn, daemon=True).start()


class Timer(_TimerCore):
    """Windows waitable-timer + APC delivery on the main thread."""

    def __init__(self, id=-1, **kwargs):
        self._running = False
        self._token = 0
        self._handle = None
        super().__init__(id, **kwargs)

    def _arm(self):
        _ensure_main_thread()
        self._token = _alloc_token(self)
        self._running = True
        _spawn(self._worker)

    def _disarm(self):
        self._running = False
        handle = self._handle
        if handle:
            kernel32.SetWaitableTimer(
                handle, ctypes.byref(_LARGE_INTEGER(0)), 0, None, None, False
            )
        if self._token:
            _free_token(self._token)
            self._token = 0

    def _worker(self):
        handle = kernel32.CreateWaitableTimerW(None, False, None)
        if not handle:
            return
        self._handle = handle
        due = _LARGE_INTEGER()
        due.QuadPart = -self._period_ms * 10000
        period_ms = self._period_ms if self._mode == Timer.PERIODIC else 0
        try:
            if not kernel32.SetWaitableTimer(
                handle,
                ctypes.byref(due),
                period_ms,
                None,
                None,
                False,
            ):
                return
            while self._running:
                rc = kernel32.WaitForSingleObject(handle, 500)
                if not self._running:
                    break
                if rc != WAIT_OBJECT_0:
                    continue
                if not kernel32.QueueUserAPC(_apc_entry, _main_thread_handle, self._token):
                    break
                if self._mode == Timer.ONE_SHOT:
                    self._running = False
                    break
        finally:
            kernel32.CloseHandle(handle)
            if self._handle is handle:
                self._handle = None
