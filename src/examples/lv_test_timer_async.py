# multimer types: async
"""
lv_test_timer_async.py

LVGL timer test — async mode.

Runs an asyncio loop (asyncio from multimer); the board's shared runtime timer
drives LVGL via lv_utils. Import display_driver inside the async main so the
event loop is already running when lv_utils subscribes its tick to the runtime.
"""

from multimer import asyncio


async def main():
    import display_driver  # noqa: F401

    from board_config import display_drv, runtime
    from lv_test_timer_common import build_ui

    build_ui("async")
    while True:
        runtime.poll()
        if runtime.quit_requested:
            break
        if getattr(display_drv, "_deinitialized", False):
            break
        await asyncio.sleep(0)


asyncio.run(main())
