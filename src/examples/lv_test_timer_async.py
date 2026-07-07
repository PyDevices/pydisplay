# multimer types: async
"""
lv_test_timer_async.py

LVGL timer test — async mode.

Runs an asyncio loop (asyncio from multimer); the board's shared broker timer
drives LVGL via lv_utils. Import display_driver inside the async main so the
event loop is already running when lv_utils subscribes its tick to the broker.
"""

# Override board_config.TIMER_ASYNC for this timer test only. Real apps normally
# set this in board_config and can omit the import/assignment below.
import board_config

board_config.TIMER_ASYNC = True

from multimer import asyncio


async def main():
    import display_driver  # noqa: F401

    from board_config import broker, display_drv
    from lv_test_timer_common import build_ui

    build_ui("async")
    while True:
        broker.poll()
        if getattr(display_drv, "_deinitialized", False):
            break
        await asyncio.sleep(0)


asyncio.run(main())
