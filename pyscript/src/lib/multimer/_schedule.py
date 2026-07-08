# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cross-platform schedule compatible with micropython.schedule."""

import sys

if sys.implementation.name in ("cpython", "circuitpython"):
    _pending = []
    _pending_lock = None

    try:
        import threading

        _main_ident = threading.main_thread().ident

        def _is_main_thread():
            return threading.current_thread().ident == _main_ident

    except ImportError:
        try:
            import _thread

            _main_ident = _thread.get_ident()

            def _is_main_thread():
                return _thread.get_ident() == _main_ident

        except ImportError:

            def _is_main_thread():
                return True

    try:
        import _thread

        _pending_lock = _thread.allocate_lock()
    except ImportError:
        pass

    def _queue(cb, arg):
        if _pending_lock is not None:
            _pending_lock.acquire()
            try:
                _pending.append((cb, arg))
            finally:
                _pending_lock.release()
        else:
            _pending.append((cb, arg))

    def _pop_pending():
        if _pending_lock is not None:
            _pending_lock.acquire()
            try:
                if not _pending:
                    return None
                return _pending.pop(0)
            finally:
                _pending_lock.release()
        if not _pending:
            return None
        return _pending.pop(0)

    def _run_pending():
        if not _is_main_thread():
            return
        while True:
            item = _pop_pending()
            if item is None:
                return
            cb, arg = item
            cb(arg)

    def schedule(cb, arg):
        if not _is_main_thread():
            _queue(cb, arg)
            return
        _run_pending()
        cb(arg)

else:
    from micropython import schedule

    def _run_pending():
        pass
