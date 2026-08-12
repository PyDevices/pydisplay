# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Opt-in asyncio facade for code which may call ``run`` inside a host loop.

PyScript and Jupyter already own an asyncio event loop. Some unchanged
MicroPython applications nevertheless call ``asyncio.run(main())`` followed by
``asyncio.new_event_loop()`` at module scope. This facade schedules the
coroutine and preserves the host loop in that case. Outside a running loop it
delegates both operations unchanged.
"""

from ._asyncio_loader import load_asyncio

# Concrete asyncio implementation (not the MicroPython ``uasyncio`` name shim).
# ``install_asyncio_compat`` re-pins this before replacing ``sys.modules``.
_backend = load_asyncio()
if _backend is None:
    raise ImportError("multimer.asyncio_compat: asyncio is not available")


def backend():
    """Return the real asyncio implementation wrapped by this facade."""
    return _backend


def _running():
    from ._asyncio_loader import loop_running

    return loop_running()


def run(coro):
    """Run normally, or schedule ``coro`` when a host loop already exists."""
    if _running():
        return _backend.create_task(coro)
    return _backend.run(coro)


def new_event_loop():
    """Create a loop normally, but never replace an active host loop."""
    if _running():
        try:
            return _backend.get_running_loop()
        except AttributeError:
            return _backend.get_event_loop()
    return _backend.new_event_loop()


def sleep(delay):
    """Sleep while ensuring a zero-delay yield reaches the browser host loop."""
    return _backend.sleep(0.001 if delay <= 0 else delay)


def sleep_ms(delay):
    """Millisecond sleep with a browser-safe minimum for cooperative yields."""
    sleeper = getattr(_backend, "sleep_ms", None)
    if sleeper is not None:
        return sleeper(1 if delay <= 0 else delay)
    return _backend.sleep(0.001 if delay <= 0 else delay / 1000)


def __getattr__(name):
    return getattr(_backend, name)
