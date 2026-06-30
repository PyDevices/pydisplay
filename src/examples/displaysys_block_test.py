# multimer types: all
"""displaysys_block_test.py"""

from random import getrandbits
try:
    from random import choice
except ImportError:
    def choice(seq):
        return seq[0]

from board_config import broker, display_drv
from eventsys import poll_quit_discarding_others
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
    blocks = []

    max_x = display_drv.width - block_size - 1
    max_y = display_drv.height - block_size - 1

    for pixel_color in [0x0000, 0xFFFF, 0xF800, 0x07E0, 0x001F, 0xFFE0, 0x07FF, 0xF81F]:
        pixel_bytes = (
            pixel_color.to_bytes(2, "big") if needs_swap else pixel_color.to_bytes(2, "little")
        )
        blocks.append(memoryview(bytearray(pixel_bytes * (block_size * block_size))))

    print("Drawing blocks on display")
    count = 0
    start_time = time.time()
    try:
        while True:
            display_drv.blit_rect(
                choice(blocks),
                randint(0, max_x),
                randint(0, max_y),
                block_size,
                block_size,
            )
            if display_drv._timer is None:
                display_drv.show()
            pump()
            count += 1
            if count % 2000 == 0:
                rate = count / (time.time() - start_time)
                print(f"blocks/sec: {rate:5.2f}")
            if poll_quit_discarding_others(broker):
                break
            sleep_ms(1)
    except KeyboardInterrupt:
        print("\nStopped.")


main()
