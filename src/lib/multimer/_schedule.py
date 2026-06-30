# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cross-platform schedule compatible with micropython.schedule."""

import sys

if sys.implementation.name in ("cpython", "circuitpython"):
    SCHEDULE_QUEUE = True
    _MAX_PENDING = 128 if sys.implementation.name == "circuitpython" else 32

    try:
        import threading

        _main_ident = threading.main_thread().ident

        def _is_main_thread():
            return threading.current_thread().ident == _main_ident

        def _make_lock():
            return threading.Lock()

    except ImportError:
        try:
            import _thread

            _main_ident = _thread.get_ident()

            def _is_main_thread():
                return _thread.get_ident() == _main_ident

            def _make_lock():
                return _thread.allocate_lock()

        except ImportError:

            def _is_main_thread():
                return True

            class _NullLock:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            def _make_lock():
                return _NullLock()

    try:
        import queue

        _pending = queue.Queue(maxsize=_MAX_PENDING)
        _QueueFull = queue.Full
        _QueueEmpty = queue.Empty

        def _put(item):
            _pending.put_nowait(item)

        def _get():
            return _pending.get_nowait()

    except ImportError:
        _pending = []
        _pending_lock = _make_lock()
        _QueueFull = RuntimeError
        _QueueEmpty = IndexError

        def _put(item):
            with _pending_lock:
                if len(_pending) >= _MAX_PENDING:
                    raise _QueueFull("schedule queue full")
                _pending.append(item)

        def _get():
            with _pending_lock:
                return _pending.pop(0)

    def schedule(cb, arg):
        if _is_main_thread():
            cb(arg)
            return
        try:
            _put((cb, arg))
        except _QueueFull as err:
            raise RuntimeError("schedule queue full") from err

    def _drain_schedule(max_items=None):
        n = 0
        while max_items is None or n < max_items:
            try:
                cb, arg = _get()
            except _QueueEmpty:
                break
            cb(arg)
            n += 1
        return n

else:
    from micropython import schedule

    SCHEDULE_QUEUE = False

    def _drain_schedule(max_items=None):
        return 0
