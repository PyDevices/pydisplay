# pyscript skip: gallery
"""
apollo.py — Apollo Guidance Computer DSKY emulator.

Written for 320×480 displays. Other resolutions may show or behave oddly
(scrolling, touch mapping, and layout assume that viewport size).
"""
import gc

try:
    # For CircuitPython and MicroPython
    from gc import mem_free
except ImportError:
    try:
        from psutil import virtual_memory

        def mem_free():
            return virtual_memory().free
    except ImportError:

        def mem_free():
            return 0


gc.collect()
mem = mem_free()
print(f"Free memory at start: {mem:,}")

from board_config import display_drv, runtime
import apollo_dsky as dsky
import time

from multimer import sleep_ms, ticks_add, ticks_diff, ticks_ms
from multimer.loop import dual_main, run

_last_time = (0, 0, 0, 0, 0, 0)
_key_busy = False
_scrolling = False
_scroll_i = 0
_scroll_end = 0
_key_release_at = None
_pending_key = None


def _init_apollo():
    dsky.init_screen()
    display_drv.show()

    dsky.write_string("42", dsky.prog_pos)
    dsky.write_string("01", dsky.verb_pos)
    dsky.write_string("23", dsky.noun_pos)
    display_drv.show()


def _update_time():
    global _last_time
    y, mo, d, h, m, s, *_ = time.localtime()
    if s != _last_time[5]:
        dsky.write_string(f"{h:02}:{m:02}:{s:02}", dsky.data2_pos)
        if (y, mo, d) != _last_time[:3]:
            dsky.write_string(f"{y-2000:02}.{mo:02}.{d:02}", dsky.data1_pos)
        _last_time = (y, mo, d, h, m, s)
        gc.collect()
        dsky.write_string(f"{mem-mem_free():7}", dsky.data3_pos)
        display_drv.show()


def _scroll_step():
    global _scrolling, _scroll_i
    if not _scrolling:
        return
    display_drv.vscsad(_scroll_i)
    display_drv.show()
    _scroll_i += 1
    if _scroll_i >= _scroll_end:
        _scrolling = False


def _start_scroll():
    global _scrolling, _scroll_i, _scroll_end
    start = display_drv.vscsad()
    if start is False:
        return
    _scroll_i = start
    _scroll_end = display_drv.height + 1
    _scrolling = True


def _key_release():
    global _key_busy, _pending_key, _key_release_at
    if _pending_key is not None:
        dsky.set_button(_pending_key, False)
        _pending_key = None
    dsky.set_acty(False)
    display_drv.show()
    _key_busy = False
    _key_release_at = None


def _handle_key(key):
    global _key_busy, _pending_key, _key_release_at
    _key_busy = True
    dsky.set_acty(True)
    dsky.set_button(key, True)
    _pending_key = key

    if key < len(dsky.light_status):
        dsky.set_light(key)
    else:
        _start_scroll()

    _key_release_at = ticks_add(ticks_ms(), 200)


def _poll_apollo():
    _update_time()

    if _key_release_at is not None and ticks_diff(_key_release_at, ticks_ms()) >= 0:
        _key_release()

    if _scrolling:
        _scroll_step()

    elist = runtime.poll() if runtime else []
    if runtime.quit_requested if runtime else False:
        return True
    if any(e.type == runtime.events.QUIT for e in elist):
        return True
    if _key_busy or _scrolling:
        return False
    if keys := dsky.keypad.read():
        for key in keys:
            _handle_key(key)
    return False


def main_sync():
    _init_apollo()
    while True:
        if _poll_apollo():
            break
        sleep_ms(1 if _scrolling else 20)


async def main_async():
    try:
        import asyncio
    except ImportError:
        import uasyncio as asyncio

    async def write_time():
        last_time = (0, 0, 0, 0, 0, 0)
        while True:
            y, mo, d, h, m, s, *_ = time.localtime()
            if s != last_time[5]:
                dsky.write_string(f"{h:02}:{m:02}:{s:02}", dsky.data2_pos)
                if (y, mo, d) != last_time[:3]:
                    dsky.write_string(f"{y-2000:02}.{mo:02}.{d:02}", dsky.data1_pos)
                last_time = (y, mo, d, h, m, s)
                gc.collect()
                dsky.write_string(f"{mem-mem_free():7}", dsky.data3_pos)
                display_drv.show()
            await asyncio.sleep(0.5)

    async def scroll():
        start = display_drv.vscsad()
        if start is False:
            return
        for i in range(start, display_drv.height + 1):
            display_drv.vscsad(i)
            display_drv.show()
            await asyncio.sleep(0.001)

    async def main_loop():
        while True:
            elist = runtime.poll() if runtime else []
            if runtime.quit_requested if runtime else False:
                break
            if any(e.type == runtime.events.QUIT for e in elist):
                break
            if keys := dsky.keypad.read():
                for key in keys:
                    dsky.set_acty(True)
                    dsky.set_button(key, True)

                    if key < len(dsky.light_status):
                        dsky.set_light(key)
                    else:
                        await scroll()

                    await asyncio.sleep(0.2)
                    dsky.set_button(key, False)
                    dsky.set_acty(False)
                    display_drv.show()
            await asyncio.sleep(0)

    async def run():
        _init_apollo()
        write_task = asyncio.create_task(write_time())
        try:
            await main_loop()
        finally:
            write_task.cancel()
            try:
                await write_task
            except asyncio.CancelledError:
                pass

    await run()


dual_main(main_sync, main_async, async_mode=runtime.timer_async)
