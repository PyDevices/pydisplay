# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Cross-platform schedule compatible with micropython.schedule."""

import sys

if sys.implementation.name in ("cpython", "circuitpython"):
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

    def schedule(cb, arg):
        if not _is_main_thread():
            raise RuntimeError("schedule from non-main thread is not supported")
        cb(arg)

else:
    from micropython import schedule
