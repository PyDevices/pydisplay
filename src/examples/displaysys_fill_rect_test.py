# multimer types: queued, sync
"""displaysys_fill_rect_test.py"""

from random import getrandbits

from board_config import display_drv
from multimer import pump, sleep_ms
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


def main():
    block_size = 32

    max_x = display_drv.width - block_size - 1
    max_y = display_drv.height - block_size - 1

    print("Drawing blocks on display")
    count = 0
    start_time = time.time()
    try:
        while True:
            display_drv.fill_rect(
                randint(0, max_x),
                randint(0, max_y),
                block_size,
                block_size,
                getrandbits(16),
            )
            if display_drv._timer is None:
                display_drv.show()
            pump()
            count += 1
            if count % 1000 == 0:
                rate = count / (time.time() - start_time)
                print(f"blocks/sec: {rate:5.2f}")
            sleep_ms(1)
    except KeyboardInterrupt:
        print("\nStopped.")


main()
