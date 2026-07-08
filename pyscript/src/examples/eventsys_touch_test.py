# multimer types: all
"""
eventsys_touch_test.py - Touch rotation test.
Tests the touch driver and finds the correct rotation masks for the touch screen.
Sets the rotation to each of 4 possible values and asks the user to touch the rectangle in each of the 4 corners.
Then it prints the touch_rotation_table that should be set in board_config.py.

On asyncio-native hosts (PyScript, Jupyter Notebook) the test runs an async main
loop that yields to the event loop so input/widget events can be dispatched.  On
MCU/desktop it runs the classic blocking loop with sleep_ms().
"""

from board_config import display_drv, runtime
import eventsys
from graphics import round_rect, text16
from multimer import sleep_ms

demo = False

FG_COLOR = -1  # white
BG_COLOR = 0  # black

text = "Touch here"
text_width = len(text) * 8

SWAP_XY = 0b001
REVERSE_X = 0b010
REVERSE_Y = 0b100

_ZONE_MASKS = {
    (0, 1, 2, 3): 0b0,
    (1, 0, 3, 2): REVERSE_X,
    (2, 3, 0, 1): REVERSE_Y,
    (3, 2, 1, 0): REVERSE_X | REVERSE_Y,
    (0, 2, 1, 3): SWAP_XY,
    (2, 0, 3, 1): SWAP_XY | REVERSE_X,
    (1, 3, 0, 2): SWAP_XY | REVERSE_Y,
    (3, 1, 2, 0): SWAP_XY | REVERSE_X | REVERSE_Y,
}


def set_rotation_table(table):
    if display_drv.touch_device is not None:
        if display_drv.touch_device.type == eventsys.TOUCH:
            display_drv.touch_device.rotation_table = table


def _draw_target(x, y, half_width, half_height):
    round_rect(
        display_drv,
        x * half_width + 10,
        y * half_height + 10,
        half_width - 20,
        half_height - 20,
        10,
        FG_COLOR,
        True,
    )
    text16(
        display_drv,
        text,
        x * half_width + ((half_width - text_width) // 2),
        y * half_height + ((half_height - 8) // 2),
        BG_COLOR,
    )
    display_drv.show()


def _clear_target(x, y, half_width, half_height):
    display_drv.fill_rect(
        x * half_width,
        y * half_height,
        half_width - 1,
        half_height - 1,
        BG_COLOR,
    )
    display_drv.show()


def _poll_touch():
    if elist := runtime.poll():
        for event in elist:
            if event.type == runtime.events.QUIT:
                raise SystemExit(0)
            if event.type == runtime.events.MOUSEBUTTONDOWN and event.button == 1:
                return event.pos
    return None


def _record_zone(touched_point, touched_zones, half_width, half_height):
    zone = (touched_point[1] // half_height) * 2 + (touched_point[0] // half_width)
    touched_zones.append(zone)
    print(f"{touched_point=} in {zone=}")


def _finish_rotation(rotation, touched_zones, touch_rotation_table):
    mask = _ZONE_MASKS.get(tuple(touched_zones))
    if mask is None:
        print("Invalid touch sequence. Starting over...\n")
        return False
    touch_rotation_table.append(mask)
    print(f"{rotation=} {mask=} ({mask:#05b})\n")
    return True


def _report(touch_rotation_table):
    if not demo:
        set_rotation_table(touch_rotation_table)
        print("Set the `touch_rotation_table` in board_config.py to the following:")
    else:
        print("Demo complete.")
    out_text = f"touch_rotation_table = {tuple(touch_rotation_table)}"
    print("    ", out_text, "\n")
    text16(
        display_drv,
        out_text,
        (display_drv.width - len(out_text) * 8) // 2,
        (display_drv.height - 8) // 2,
        FG_COLOR,
    )


def loop():
    display_drv.fill_rect(0, 0, display_drv.width - 1, display_drv.height - 1, BG_COLOR)

    print("Touch the rectangle in each corner for 4 rotations.\n")

    touch_rotation_table = []

    for rotation in range(0, 360, 90):
        touched_zones = []
        display_drv.rotation = rotation

        half_width = display_drv.width // 2
        half_height = display_drv.height // 2

        for y in range(2):
            for x in range(2):
                _draw_target(x, y, half_width, half_height)
                touched_point = None
                while not touched_point:
                    touched_point = _poll_touch()
                    sleep_ms(0)
                    sleep_ms(1)
                _record_zone(touched_point, touched_zones, half_width, half_height)
                _clear_target(x, y, half_width, half_height)

        if not _finish_rotation(rotation, touched_zones, touch_rotation_table):
            return False

    _report(touch_rotation_table)
    return True


async def loop_async():
    try:
        import asyncio
    except ImportError:
        import uasyncio as asyncio

    display_drv.fill_rect(0, 0, display_drv.width - 1, display_drv.height - 1, BG_COLOR)

    print("Touch the rectangle in each corner for 4 rotations.\n")

    touch_rotation_table = []

    for rotation in range(0, 360, 90):
        touched_zones = []
        display_drv.rotation = rotation

        half_width = display_drv.width // 2
        half_height = display_drv.height // 2

        for y in range(2):
            for x in range(2):
                _draw_target(x, y, half_width, half_height)
                touched_point = None
                while not touched_point:
                    touched_point = _poll_touch()
                    await asyncio.sleep(0.02)
                _record_zone(touched_point, touched_zones, half_width, half_height)
                _clear_target(x, y, half_width, half_height)

        if not _finish_rotation(rotation, touched_zones, touch_rotation_table):
            return False

    _report(touch_rotation_table)
    return True


async def main_async():
    from multimer import sleep_ms

    completed = False
    while not completed:
        display_drv.show()
        completed = await loop_async()
        await sleep_ms(0)


def run_sync():
    completed = False
    try:
        while not completed:
            display_drv.show()
            completed = loop()
            sleep_ms(0)
            sleep_ms(1)
    except KeyboardInterrupt:
        print("\nStopped.")


if not demo:
    set_rotation_table((0, 0, 0, 0))

if runtime.timer_async:
    # On a host with a running loop (Jupyter, PyScript) this schedules the test
    # as a background task and returns; otherwise it runs to completion.
    from multimer import run

    run(main_async)
else:
    run_sync()
