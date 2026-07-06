# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Small optional application-loop helpers."""


def run_forever(poll, delay_ms=20):
    """Run a polling loop until ``poll`` returns true."""
    from . import sleep_ms

    while True:
        if poll():
            break
        sleep_ms(delay_ms)


async def run_forever_async(poll, delay_ms=20):
    """Async version of ``run_forever``."""
    from . import asyncio
    from ._schedule import _run_pending
    from ._select import _drain as _backend_drain

    while True:
        if poll():
            break
        _run_pending()
        if _backend_drain is not None:
            _backend_drain()
        await asyncio.sleep(delay_ms / 1000)  # type: ignore[misc]


def dual_main(sync_main, async_main, async_mode=False):
    """
    Start either a sync or async application entrypoint.

    In async mode, the async entrypoint is scheduled on the active multimer
    asyncio loop and the created task is returned. In sync mode, the sync
    entrypoint is called immediately and its return value is returned.
    """
    if async_mode:
        from . import asyncio

        return asyncio.create_task(async_main())
    return sync_main()
