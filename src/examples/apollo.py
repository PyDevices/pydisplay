import gc

try:
    # For CircuitPython and MicroPython
    from gc import mem_free
except ImportError:
    # For CPython
    from psutil import virtual_memory

    def mem_free():
        return virtual_memory().free


gc.collect()
mem = mem_free()
print(f"Free memory at start: {mem:,}")

from board_config import display_drv, broker  # noqa: E402
import apollo_dsky as dsky  # noqa: E402
import time  # noqa: E402
import asyncio  # noqa: E402


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
        await asyncio.sleep(0.5)


async def scroll():
    if vscsad := display_drv.vscsad():
        scroll_range = (vscsad, display_drv.height + 1, 1)
    else:
        scroll_range = (display_drv.height, dsky.height - 1, -1)
    for i in range(*scroll_range):
        display_drv.vscsad(i)
        await asyncio.sleep(0.001)


async def main():
    dsky.init_screen()

    dsky.write_string("42", dsky.prog_pos)
    dsky.write_string("01", dsky.verb_pos)
    dsky.write_string("23", dsky.noun_pos)

    while True:
        await asyncio.sleep(0)
        broker.poll()
        if (keys := dsky.keypad.read()) is not None:
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


loop = asyncio.get_event_loop()
tasks = [
    loop.create_task(main()),
    loop.create_task(write_time()),
]
if hasattr(loop, "is_running") and loop.is_running():
    pass
else:
    if hasattr(loop, "run_forever"):
        loop.run_forever()
