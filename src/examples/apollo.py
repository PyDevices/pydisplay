# multimer types: async
# pyscript binaries: apollo_dsky/Apollo_DSKY_interface.bmp
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

from board_config import TIMER_ASYNC, display_drv, broker
import apollo_dsky as dsky
import time

from multimer import Timer
from multimer.loop import dual_main, run_forever

_last_time = (0, 0, 0, 0, 0, 0)
_key_busy = False
_scrolling = False
_scroll_i = 0
_scroll_end = 0
_scroll_timer = Timer(-1)
_key_timer = Timer(-2)
_pending_key = None


def _init_apollo():
    dsky.init_screen()
    display_drv.show()

    dsky.write_string("42", dsky.prog_pos)
    dsky.write_string("01", dsky.verb_pos)
    dsky.write_string("23", dsky.noun_pos)
    display_drv.show()


def _write_time_tick(_=None):
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


def _scroll_tick(_=None):
    global _scrolling, _scroll_i
    if not _scrolling:
        return
    display_drv.vscsad(_scroll_i)
    display_drv.show()
    _scroll_i += 1
    if _scroll_i >= _scroll_end:
        _scrolling = False
        _scroll_timer.deinit()


def _start_scroll():
    global _scrolling, _scroll_i, _scroll_end
    start = display_drv.vscsad()
    if start is False:
        return
    _scroll_i = start
    _scroll_end = display_drv.height + 1
    _scrolling = True
    _scroll_timer.init(mode=Timer.PERIODIC, period=1, callback=_scroll_tick)


def _key_release(_=None):
    global _key_busy, _pending_key
    if _pending_key is not None:
        dsky.set_button(_pending_key, False)
        _pending_key = None
    dsky.set_acty(False)
    display_drv.show()
    _key_busy = False


def _handle_key(key):
    global _key_busy, _pending_key
    _key_busy = True
    dsky.set_acty(True)
    dsky.set_button(key, True)
    _pending_key = key

    if key < len(dsky.light_status):
        dsky.set_light(key)
    else:
        _start_scroll()

    _key_timer.init(mode=Timer.ONE_SHOT, period=200, callback=_key_release)


def _poll_apollo():
    if elist := broker.poll():
        if any(e.type == broker.events.QUIT for e in elist):
            return True
    if _key_busy or _scrolling:
        return False
    if keys := dsky.keypad.read():
        for key in keys:
            _handle_key(key)
    return False


def main_sync():
    _init_apollo()
    timer = Timer(-1)
    timer.init(mode=Timer.PERIODIC, period=500, callback=_write_time_tick)
    try:
        run_forever(_poll_apollo)
    finally:
        timer.deinit()


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
            if elist := broker.poll():
                if any(e.type == broker.events.QUIT for e in elist):
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


dual_main(main_sync, main_async, async_mode=TIMER_ASYNC)
