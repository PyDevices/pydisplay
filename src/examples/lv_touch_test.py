# pyscript gallery: async
"""
lv_touch_test.py

Touch/rotation grid for LVGL. Follows ``runtime.timer_async`` — does not read
or write environment variables.
"""

from board_config import display_drv, runtime
from multimer.loop import dual_main
import time

alignments = None  # filled in _build_ui after lvgl import


def _build_ui():
    import lvgl as lv

    # Pause shared LVGL task_handler while constructing widgets (not re-entrant).
    # Same pattern as lv_test_timer.build_ui — under matrix load, librt ticks
    # during widget create can SIGSEGV on CPython (exit_-11).
    inst = None
    try:
        import lv_utils

        inst = lv_utils.event_loop.current_instance()
    except ImportError:
        inst = None
    if inst is not None:
        inst.disable()
    try:
        global alignments
        alignments = (
            (lv.ALIGN.TOP_LEFT, 0, 0),
            (lv.ALIGN.TOP_MID, 0, 0),
            (lv.ALIGN.TOP_RIGHT, 0, 0),
            (lv.ALIGN.LEFT_MID, 0, 0),
            (lv.ALIGN.CENTER, 0, 0),
            (lv.ALIGN.RIGHT_MID, 0, 0),
            (lv.ALIGN.BOTTOM_LEFT, 0, 0),
            (lv.ALIGN.BOTTOM_MID, 0, 0),
            (lv.ALIGN.BOTTOM_RIGHT, 0, 0),
        )

        style_default = lv.style_t()
        style_default.init()
        style_default.set_width(lv.pct(33))
        style_default.set_height(lv.pct(33))
        style_default.set_bg_color(lv.palette_main(lv.PALETTE.BLUE))

        style_pressed = lv.style_t()
        style_pressed.init()
        style_pressed.set_transform_width(-10)
        style_pressed.set_transform_height(-10)
        style_pressed.set_bg_color(lv.palette_main(lv.PALETTE.GREEN))

        style_focused = lv.style_t()
        style_focused.init()
        style_focused.set_bg_color(lv.palette_main(lv.PALETTE.RED))

        parent = lv.screen_active()

        for i, alignment in enumerate(alignments, start=1):
            btn = lv.button(parent)
            btn.align(*alignment)
            btn.add_style(style_default, 0)
            btn.add_style(style_pressed, lv.STATE.PRESSED)
            btn.add_style(style_focused, lv.STATE.FOCUSED)
            label = lv.label(btn)
            label.set_text(f"Btn{i}")
            label.center()
    finally:
        if inst is not None:
            inst.enable()


def _setup():
    import display_driver  # noqa: F401

    _build_ui()


def _done():
    if runtime.quit_requested:
        return True
    if getattr(display_drv, "_deinitialized", False):
        return True
    return False


def main_sync():
    _setup()
    # Avoid multimer.sleep_ms / runtime.poll on the main thread while a
    # signal- or SDL-driven LVGL tick is live (CPython librt segfault; CP races).
    # Matrix quit uses the test-mode deadline hook (cooperative LVGL path).
    from multimer import run_deadline_hook

    while True:
        run_deadline_hook()
        if _done():
            break
        time.sleep(0.01)


async def main_async():
    _setup()
    from multimer import asyncio

    while True:
        runtime.poll()
        if _done():
            break
        await asyncio.sleep(0)


dual_main(main_sync, main_async, async_mode=runtime.timer_async)
