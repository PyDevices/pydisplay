"""displaysys_fill_rect_test.py"""

from random import getrandbits

from board_config import display_drv, runtime
from multimer.loop import run_forever
import gc
import time


def randint(a, b):
    span = b - a + 1
    if span <= 1:
        return a
    bits = 0
    n = span - 1
    while n:
        bits += 1
        n >>= 1
    return a + getrandbits(bits) % span


gc.collect()
if display_drv.requires_byteswap:
    needs_swap = display_drv.disable_auto_byteswap(True)
else:
    needs_swap = False


def _setup():
    block_size = 32

    max_x = display_drv.width - block_size - 1
    max_y = display_drv.height - block_size - 1

    print("Drawing blocks on display")
    st = {"count": 0, "start_time": time.time()}

    def poll():
        display_drv.fill_rect(
            randint(0, max_x),
            randint(0, max_y),
            block_size,
            block_size,
            getrandbits(16),
        )
        if getattr(runtime, "_timer", None) is None:
            display_drv.show()
        st["count"] += 1
        if st["count"] % 1000 == 0:
            rate = st["count"] / (time.time() - st["start_time"])
            print(f"blocks/sec: {rate:5.2f}")
        if runtime:
            runtime.poll()
        if runtime.quit_requested if runtime else False:
            return True
        return False

    return poll


# run_forever blocks on desktop/MCU but yields to the event loop on PyScript
# and Jupyter (runtime.timer_async), so the browser main thread stays live.
run_forever(_setup(), delay_ms=1)
