# multimer types: async
"""
Simple calculator example to demonstrate the use of graphics.FrameBuffer
"""

from board_config import display_drv, broker
from touch_keypad import Keypad
from graphics import FrameBuffer, RGB565
from eventsys.keys import Keys
from palettes import get_palette
from multimer import ONE_SHOT, Timer, dual_main, run_forever


def _build_calculator():
    # Setup variables
    FONT_WIDTH = 8
    WIDTH = display_drv.width
    HEIGHT = display_drv.height
    BPP = display_drv.color_depth // 8  # Bytes per pixel
    ROWS = 6
    COLS = 4
    ROW_HEIGHT = HEIGHT // ROWS
    COL_WIDTH = WIDTH // COLS
    PAD = min([ROW_HEIGHT, COL_WIDTH]) // 16
    PAD_X2 = 2 * PAD
    PAD_X3 = 3 * PAD
    PAD_X4 = 4 * PAD
    BTN_WIDTH = COL_WIDTH - PAD_X2
    BTN_HEIGHT = ROW_HEIGHT - PAD_X2
    LINE_WIDTH = WIDTH - PAD_X2
    LINE_HEIGHT = (ROW_HEIGHT - PAD_X2) // 2

    # Get the palette
    pal = get_palette(name="material_design")

    # fmt: off
    # Define the button labels
    button_labels = [
        "Sqrt", "%", "+/-", "C",
        "7", "8", "9", "/",
        "4", "5", "6", "*",
        "1", "2", "3", "-",
        "0", ".", "=", "+",
    ]

    # Define the button codes
    button_codes = [
        Keys.K_s,           Keys.K_p,           Keys.K_m,           Keys.K_c,
        Keys.K_KP_7,        Keys.K_KP_8,        Keys.K_KP_9,        Keys.K_KP_DIVIDE,
        Keys.K_KP_4,        Keys.K_KP_5,        Keys.K_KP_6,        Keys.K_KP_MULTIPLY,
        Keys.K_KP_1,        Keys.K_KP_2,        Keys.K_KP_3,        Keys.K_KP_MINUS,
        Keys.K_KP_0,        Keys.K_KP_PERIOD,   Keys.K_KP_ENTER,    Keys.K_KP_PLUS,
    ]
    # fmt: on

    button_offset = [None] * COLS

    # Create the keypad
    keypad = Keypad(
        broker,
        0,
        0,
        display_drv.width,
        display_drv.height,
        COLS,
        ROWS,
        button_offset + button_codes,
    )

    # Function to draw a button
    def draw_button(xpos, ypos, label, pressed=False):
        if pressed:
            fgcolor, btncolor = pal.WHITE, pal.BLUE
        else:
            if label in "0123456789.":
                fgcolor, btncolor = pal.BLACK, pal.WHITE
            elif label in "+-*/":
                fgcolor, btncolor = pal.BLACK, pal.AMBER
            elif label == "=":
                fgcolor, btncolor = pal.BLACK, pal.BLUE
            else:
                fgcolor, btncolor = pal.BLACK, pal.BLUE_GREY

        button_fb.fill(pal.BLACK)
        button_fb.round_rect(
            PAD, PAD, BTN_WIDTH - PAD_X2, BTN_HEIGHT - PAD_X2, PAD_X4, btncolor, True
        )
        button_fb.text16(label, PAD_X3, PAD_X3, fgcolor)
        display_drv.blit_rect(
            button_ba,
            xpos * COL_WIDTH + PAD,
            ypos * ROW_HEIGHT + PAD,
            BTN_WIDTH,
            BTN_HEIGHT,
        )

    # Function to display the result line right justified
    def show_result(result):
        x_start = LINE_WIDTH - (len(str(result)) * FONT_WIDTH + PAD_X2)
        line_fb.fill(pal.BLACK)
        line_fb.text16(str(result), x_start, PAD, pal.WHITE)
        display_drv.blit_rect(line_ba, PAD, PAD, LINE_WIDTH, LINE_HEIGHT)

    # Function to display the input line right justified
    def show_input(input):
        x_start = LINE_WIDTH - (len(input) * FONT_WIDTH + PAD_X2)
        line_fb.fill(pal.BLACK)
        line_fb.text16(input, x_start, PAD, pal.YELLOW)
        display_drv.blit_rect(line_ba, PAD, LINE_HEIGHT + PAD, LINE_WIDTH, LINE_HEIGHT)

    # Create the framebuffers
    line_ba = bytearray(LINE_WIDTH * LINE_HEIGHT * BPP)
    line_fb = FrameBuffer(line_ba, LINE_WIDTH, LINE_HEIGHT, RGB565)
    button_ba = bytearray(BTN_WIDTH * BTN_HEIGHT * BPP)
    button_fb = FrameBuffer(button_ba, BTN_WIDTH, BTN_HEIGHT, RGB565)

    # Clear the screen
    display_drv.fill(pal.BLACK)

    # Draw the Window
    display_drv.fill_rect(0, 0, WIDTH, ROW_HEIGHT, pal.LIGHT_BLUE)
    display_drv.fill_rect(PAD // 2, PAD // 2, WIDTH - PAD, ROW_HEIGHT - PAD, pal.BLUE_GREY)

    # Draw the buttons, saving their positions.
    button_pos = {}
    for i, button in enumerate(zip(button_codes, button_labels)):
        x = i % COLS
        y = i // COLS + 1
        code, label = button
        button_pos[code] = (x, y)
        draw_button(x, y, label)

    result = 0
    pending_operation = ""
    input = "0"
    editable = True
    pending_release = None
    release_timer = Timer(-1)

    def release_button(_=None):
        nonlocal pending_release
        if pending_release is None:
            return
        x, y, label = pending_release
        pending_release = None
        draw_button(x, y, label, False)
        display_drv.show()

    show_result('Demo only.  Expect "quirks"!')
    show_input(input)
    display_drv.show()

    def poll():
        nonlocal result, pending_operation, input, editable, pending_release
        if elist := broker.poll():
            if any(e.type == broker.events.QUIT for e in elist):
                return True
        if codes := keypad.read():
            for code in codes:
                if code not in button_codes:
                    continue
                x, y = button_pos[code]
                label = button_labels[button_codes.index(code)]
                draw_button(x, y, label, True)

                if label in "0123456789.":
                    if not editable:
                        input = label
                    elif input == "0" and label != ".":
                        input = label
                    elif label == "." and "." not in input:
                        input += label
                    elif label != ".":
                        input += label
                    editable = True
                elif label == "C":
                    if input == "0":
                        result = 0
                        pending_operation = ""
                    else:
                        input = "0"
                    editable = True
                elif label == "+/-":
                    if input != "0":
                        input = str(-float(input))
                elif label in "+-*/=":
                    editable = True
                    if pending_operation:
                        try:
                            result = eval(f"{result}{pending_operation}{input}")
                        except ZeroDivisionError:
                            result = "Error: division by zero"
                            editable = False
                    else:
                        if input != "0":
                            result = float(input)
                    if label == "=":
                        pending_operation = ""
                    else:
                        pending_operation = label
                    input = "0"
                elif label == "%":
                    input = str(float(input) / 100)
                    editable = False
                elif label == "Sqrt":
                    if float(input) < 0:
                        result = "Error: sqrt of negative number"
                    else:
                        input = str(float(input) ** 0.5)
                    editable = False
                else:
                    print("Unknown label")
                show_result(result)
                show_input(input)
                pending_release = (x, y, label)
                release_timer.init(mode=ONE_SHOT, period=150, callback=release_button)
                display_drv.show()
        return False

    return poll


def main_sync():
    poll = _build_calculator()
    run_forever(poll, delay_ms=20)


async def main_async():
    try:
        import asyncio
    except ImportError:
        import uasyncio as asyncio

    # Setup variables
    FONT_WIDTH = 8
    WIDTH = display_drv.width
    HEIGHT = display_drv.height
    BPP = display_drv.color_depth // 8  # Bytes per pixel
    ROWS = 6
    COLS = 4
    ROW_HEIGHT = HEIGHT // ROWS
    COL_WIDTH = WIDTH // COLS
    PAD = min([ROW_HEIGHT, COL_WIDTH]) // 16
    PAD_X2 = 2 * PAD
    PAD_X3 = 3 * PAD
    PAD_X4 = 4 * PAD
    BTN_WIDTH = COL_WIDTH - PAD_X2
    BTN_HEIGHT = ROW_HEIGHT - PAD_X2
    LINE_WIDTH = WIDTH - PAD_X2
    LINE_HEIGHT = (ROW_HEIGHT - PAD_X2) // 2

    # Get the palette
    pal = get_palette(name="material_design")

    # fmt: off
    button_labels = [
        "Sqrt", "%", "+/-", "C",
        "7", "8", "9", "/",
        "4", "5", "6", "*",
        "1", "2", "3", "-",
        "0", ".", "=", "+",
    ]

    button_codes = [
        Keys.K_s,           Keys.K_p,           Keys.K_m,           Keys.K_c,
        Keys.K_KP_7,        Keys.K_KP_8,        Keys.K_KP_9,        Keys.K_KP_DIVIDE,
        Keys.K_KP_4,        Keys.K_KP_5,        Keys.K_KP_6,        Keys.K_KP_MULTIPLY,
        Keys.K_KP_1,        Keys.K_KP_2,        Keys.K_KP_3,        Keys.K_KP_MINUS,
        Keys.K_KP_0,        Keys.K_KP_PERIOD,   Keys.K_KP_ENTER,    Keys.K_KP_PLUS,
    ]
    # fmt: on

    button_offset = [None] * COLS

    keypad = Keypad(
        broker,
        0,
        0,
        display_drv.width,
        display_drv.height,
        COLS,
        ROWS,
        button_offset + button_codes,
    )

    def draw_button(xpos, ypos, label, pressed=False):
        if pressed:
            fgcolor, btncolor = pal.WHITE, pal.BLUE
        else:
            if label in "0123456789.":
                fgcolor, btncolor = pal.BLACK, pal.WHITE
            elif label in "+-*/":
                fgcolor, btncolor = pal.BLACK, pal.AMBER
            elif label == "=":
                fgcolor, btncolor = pal.BLACK, pal.BLUE
            else:
                fgcolor, btncolor = pal.BLACK, pal.BLUE_GREY

        button_fb.fill(pal.BLACK)
        button_fb.round_rect(
            PAD, PAD, BTN_WIDTH - PAD_X2, BTN_HEIGHT - PAD_X2, PAD_X4, btncolor, True
        )
        button_fb.text16(label, PAD_X3, PAD_X3, fgcolor)
        display_drv.blit_rect(
            button_ba,
            xpos * COL_WIDTH + PAD,
            ypos * ROW_HEIGHT + PAD,
            BTN_WIDTH,
            BTN_HEIGHT,
        )

    def show_result(result):
        x_start = LINE_WIDTH - (len(str(result)) * FONT_WIDTH + PAD_X2)
        line_fb.fill(pal.BLACK)
        line_fb.text16(str(result), x_start, PAD, pal.WHITE)
        display_drv.blit_rect(line_ba, PAD, PAD, LINE_WIDTH, LINE_HEIGHT)

    def show_input(input):
        x_start = LINE_WIDTH - (len(input) * FONT_WIDTH + PAD_X2)
        line_fb.fill(pal.BLACK)
        line_fb.text16(input, x_start, PAD, pal.YELLOW)
        display_drv.blit_rect(line_ba, PAD, LINE_HEIGHT + PAD, LINE_WIDTH, LINE_HEIGHT)

    line_ba = bytearray(LINE_WIDTH * LINE_HEIGHT * BPP)
    line_fb = FrameBuffer(line_ba, LINE_WIDTH, LINE_HEIGHT, RGB565)
    button_ba = bytearray(BTN_WIDTH * BTN_HEIGHT * BPP)
    button_fb = FrameBuffer(button_ba, BTN_WIDTH, BTN_HEIGHT, RGB565)

    display_drv.fill(pal.BLACK)
    display_drv.fill_rect(0, 0, WIDTH, ROW_HEIGHT, pal.LIGHT_BLUE)
    display_drv.fill_rect(PAD // 2, PAD // 2, WIDTH - PAD, ROW_HEIGHT - PAD, pal.BLUE_GREY)

    button_pos = {}
    for i, button in enumerate(zip(button_codes, button_labels)):
        x = i % COLS
        y = i // COLS + 1
        code, label = button
        button_pos[code] = (x, y)
        draw_button(x, y, label)

    result = 0
    pending_operation = ""
    input = "0"
    editable = True

    show_result('Demo only.  Expect "quirks"!')
    show_input(input)
    display_drv.show()

    while True:
        if elist := broker.poll():
            if any(e.type == broker.events.QUIT for e in elist):
                break
        if codes := keypad.read():
            for code in codes:
                if code not in button_codes:
                    continue
                x, y = button_pos[code]
                label = button_labels[button_codes.index(code)]
                draw_button(x, y, label, True)

                if label in "0123456789.":
                    if not editable:
                        input = label
                    elif input == "0" and label != ".":
                        input = label
                    elif label == "." and "." not in input:
                        input += label
                    elif label != ".":
                        input += label
                    editable = True
                elif label == "C":
                    if input == "0":
                        result = 0
                        pending_operation = ""
                    else:
                        input = "0"
                    editable = True
                elif label == "+/-":
                    if input != "0":
                        input = str(-float(input))
                elif label in "+-*/=":
                    editable = True
                    if pending_operation:
                        try:
                            result = eval(f"{result}{pending_operation}{input}")
                        except ZeroDivisionError:
                            result = "Error: division by zero"
                            editable = False
                    else:
                        if input != "0":
                            result = float(input)
                    if label == "=":
                        pending_operation = ""
                    else:
                        pending_operation = label
                    input = "0"
                elif label == "%":
                    input = str(float(input) / 100)
                    editable = False
                elif label == "Sqrt":
                    if float(input) < 0:
                        result = "Error: sqrt of negative number"
                    else:
                        input = str(float(input) ** 0.5)
                    editable = False
                else:
                    print("Unknown label")
                show_result(result)
                show_input(input)
                await asyncio.sleep(0.15)
                draw_button(x, y, label, False)
                display_drv.show()
        await asyncio.sleep(0.02)


from board_config import TIMER_ASYNC

dual_main(main_sync, main_async, async_mode=TIMER_ASYNC)
