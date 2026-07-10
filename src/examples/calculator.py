# pyscript gallery: async
"""
Simple calculator example to demonstrate the use of graphics.FrameBuffer
"""

from board_config import display_drv, runtime
from palettes import get_palette
from touch_keypad import Keypad

from eventsys.keys import Keys
from graphics import RGB565, FrameBuffer
from multimer import Timer
from multimer.loop import dual_main, run_forever


class _Calculator:
    FONT_WIDTH = 8
    ROWS = 6
    COLS = 4

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

    def __init__(self):
        self.width = display_drv.width
        self.height = display_drv.height
        self.bpp = display_drv.color_depth // 8
        self.row_height = self.height // self.ROWS
        self.col_width = self.width // self.COLS
        self.pad = min([self.row_height, self.col_width]) // 16
        self.pad_x2 = 2 * self.pad
        self.pad_x3 = 3 * self.pad
        self.pad_x4 = 4 * self.pad
        self.btn_width = self.col_width - self.pad_x2
        self.btn_height = self.row_height - self.pad_x2
        self.line_width = self.width - self.pad_x2
        self.line_height = (self.row_height - self.pad_x2) // 2
        self.pal = get_palette(name="material_design")
        self.keypad = Keypad(
            runtime,
            0,
            0,
            display_drv.width,
            display_drv.height,
            self.COLS,
            self.ROWS,
            [None] * self.COLS + self.button_codes,
        )
        self.line_ba = bytearray(self.line_width * self.line_height * self.bpp)
        self.line_fb = FrameBuffer(self.line_ba, self.line_width, self.line_height, RGB565)
        self.button_ba = bytearray(self.btn_width * self.btn_height * self.bpp)
        self.button_fb = FrameBuffer(self.button_ba, self.btn_width, self.btn_height, RGB565)
        self.button_pos = {}
        self.result = 0
        self.pending_operation = ""
        self.input = "0"
        self.editable = True
        self.draw()

    def draw(self):
        display_drv.fill(self.pal.BLACK)
        display_drv.fill_rect(0, 0, self.width, self.row_height, self.pal.LIGHT_BLUE)
        display_drv.fill_rect(
            self.pad // 2,
            self.pad // 2,
            self.width - self.pad,
            self.row_height - self.pad,
            self.pal.BLUE_GREY,
        )
        for i, button in enumerate(zip(self.button_codes, self.button_labels)):
            x = i % self.COLS
            y = i // self.COLS + 1
            code, label = button
            self.button_pos[code] = (x, y)
            self.draw_button(x, y, label)
        self.show_result('Demo only.  Expect "quirks"!')
        self.show_input(self.input)
        display_drv.show()

    def draw_button(self, xpos, ypos, label, pressed=False):
        if pressed:
            fgcolor, btncolor = self.pal.WHITE, self.pal.BLUE
        else:
            if label in "0123456789.":
                fgcolor, btncolor = self.pal.BLACK, self.pal.WHITE
            elif label in "+-*/":
                fgcolor, btncolor = self.pal.BLACK, self.pal.AMBER
            elif label == "=":
                fgcolor, btncolor = self.pal.BLACK, self.pal.BLUE
            else:
                fgcolor, btncolor = self.pal.BLACK, self.pal.BLUE_GREY

        self.button_fb.fill(self.pal.BLACK)
        self.button_fb.round_rect(
            self.pad,
            self.pad,
            self.btn_width - self.pad_x2,
            self.btn_height - self.pad_x2,
            self.pad_x4,
            btncolor,
            True,
        )
        self.button_fb.text16(label, self.pad_x3, self.pad_x3, fgcolor)
        display_drv.blit_rect(
            self.button_ba,
            xpos * self.col_width + self.pad,
            ypos * self.row_height + self.pad,
            self.btn_width,
            self.btn_height,
        )

    def show_result(self, result):
        x_start = self.line_width - (len(str(result)) * self.FONT_WIDTH + self.pad_x2)
        self.line_fb.fill(self.pal.BLACK)
        self.line_fb.text16(str(result), x_start, self.pad, self.pal.WHITE)
        display_drv.blit_rect(self.line_ba, self.pad, self.pad, self.line_width, self.line_height)

    def show_input(self, input):
        x_start = self.line_width - (len(input) * self.FONT_WIDTH + self.pad_x2)
        self.line_fb.fill(self.pal.BLACK)
        self.line_fb.text16(input, x_start, self.pad, self.pal.YELLOW)
        display_drv.blit_rect(
            self.line_ba,
            self.pad,
            self.line_height + self.pad,
            self.line_width,
            self.line_height,
        )

    def poll_quit(self):
        import eventsys

        if runtime is None:
            return False
        elist = runtime.poll()
        if runtime.quit_requested:
            return True
        return elist and any(e.type == eventsys.QUIT for e in elist)

    def read_presses(self):
        presses = []
        if codes := self.keypad.read():
            for code in codes:
                if code not in self.button_codes:
                    continue
                x, y = self.button_pos[code]
                label = self.button_labels[self.button_codes.index(code)]
                self.handle_press(x, y, label)
                presses.append((x, y, label))
        return presses

    def handle_press(self, x, y, label):
        self.draw_button(x, y, label, True)

        if label in "0123456789.":
            if not self.editable or (self.input == "0" and label != "."):
                self.input = label
            elif (label == "." and "." not in self.input) or label != ".":
                self.input += label
            self.editable = True
        elif label == "C":
            if self.input == "0":
                self.result = 0
                self.pending_operation = ""
            else:
                self.input = "0"
            self.editable = True
        elif label == "+/-":
            if self.input != "0":
                self.input = str(-float(self.input))
        elif label in "+-*/=":
            self.editable = True
            if self.pending_operation:
                try:
                    self.result = eval(f"{self.result}{self.pending_operation}{self.input}")
                except ZeroDivisionError:
                    self.result = "Error: division by zero"
                    self.editable = False
            else:
                if self.input != "0":
                    self.result = float(self.input)
            self.pending_operation = "" if label == "=" else label
            self.input = "0"
        elif label == "%":
            self.input = str(float(self.input) / 100)
            self.editable = False
        elif label == "Sqrt":
            if float(self.input) < 0:
                self.result = "Error: sqrt of negative number"
            else:
                self.input = str(float(self.input) ** 0.5)
            self.editable = False
        else:
            print("Unknown label")
        self.show_result(self.result)
        self.show_input(self.input)
        display_drv.show()

    def release_button(self, x, y, label):
        self.draw_button(x, y, label, False)
        display_drv.show()


def _sync_poll(calc):
    pending_release = None
    release_timer = Timer(-1)

    def release_button(_=None):
        nonlocal pending_release
        if pending_release is None:
            return
        x, y, label = pending_release
        pending_release = None
        calc.release_button(x, y, label)

    def poll():
        nonlocal pending_release
        if calc.poll_quit():
            return True
        for release in calc.read_presses():
            pending_release = release
            release_timer.init(mode=Timer.ONE_SHOT, period=150, callback=release_button)
        return False

    return poll


def main_sync():
    calc = _Calculator()
    run_forever(_sync_poll(calc), delay_ms=20)


async def main_async():
    try:
        import asyncio
    except ImportError:
        import uasyncio as asyncio

    calc = _Calculator()
    while True:
        if calc.poll_quit():
            break
        for press in calc.read_presses():
            await asyncio.sleep(0.15)
            calc.release_button(*press)
        await asyncio.sleep(0.02)


dual_main(main_sync, main_async, async_mode=runtime.timer_async)
