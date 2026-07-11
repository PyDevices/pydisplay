# pyscript modules: calc_engine
"""
calc_graphics
====================================================
Dark-theme pocket calculator drawn with ``graphics.FrameBuffer``.

Shares :class:`calc_engine.CalcEngine` with the pdwidgets and LVGL front ends.
All geometry (padding, button size, font scale, display band) is derived from
``display_drv.width`` / ``height`` so the UI scales from 320x480 up through
640x960 and similar desktop sizes.
"""

import sys

_EXAMPLES = __file__.replace("\\", "/").rsplit("/", 1)[0]
if _EXAMPLES not in sys.path:
    sys.path.insert(0, _EXAMPLES)

from board_config import display_drv, runtime
from calc_engine import CalcEngine
from eventsys.keys import Keys
from graphics import RGB565, FrameBuffer
from multimer import Timer
from multimer.loop import dual_main, run_forever
from palettes import get_palette
from touch_keypad import Keypad


# Button grid: 1 display row + 6 keypad rows, 4 columns.
# Row 6 draws sqrt / % as two double-wide buttons (cells 0-1 and 2-3).
# Both cells of a wide button share the same label so touch hits either half.
_LABELS = [
    "CE", "C", "BS", "/",
    "7", "8", "9", "*",
    "4", "5", "6", "-",
    "1", "2", "3", "+",
    "+/-", "0", ".", "=",
    "sqrt", "sqrt", "%", "%",
]

# fmt: off
_CODES = [
    Keys.K_ESCAPE,       Keys.K_c,            Keys.K_BACKSPACE,    Keys.K_KP_DIVIDE,
    Keys.K_KP_7,         Keys.K_KP_8,         Keys.K_KP_9,         Keys.K_KP_MULTIPLY,
    Keys.K_KP_4,         Keys.K_KP_5,         Keys.K_KP_6,         Keys.K_KP_MINUS,
    Keys.K_KP_1,         Keys.K_KP_2,         Keys.K_KP_3,         Keys.K_KP_PLUS,
    Keys.K_KP_PLUSMINUS, Keys.K_KP_0,         Keys.K_KP_PERIOD,    Keys.K_KP_ENTER,
    Keys.K_s,            Keys.K_KP_POWER,     Keys.K_p,            Keys.K_KP_PERCENT,
]
# fmt: on

_KEY_ALIASES = {
    Keys.K_RETURN: "=",
    Keys.K_KP_EQUALS: "=",
    Keys.K_SLASH: "/",
    Keys.K_ASTERISK: "*",
    Keys.K_MINUS: "-",
    Keys.K_EQUALS: "=",
    Keys.K_PERIOD: ".",
    Keys.K_PERCENT: "%",
}


def _c565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class _Calculator:
    COLS = 4
    BTN_ROWS = 6
    ROWS = 1 + BTN_ROWS  # display band + buttons
    FONT_W = 8
    FONT_H = 16

    def __init__(self):
        self.width = display_drv.width
        self.height = display_drv.height
        self.bpp = display_drv.color_depth // 8
        self.unit = min(self.width, self.height)

        # Scale factors from a 320x480 reference panel.
        self.pad = max(2, self.unit // 80)
        self.radius = max(4, self.unit // 40)
        self.row_h = self.height // self.ROWS
        self.col_w = self.width // self.COLS
        self.btn_w = self.col_w - 2 * self.pad
        self.btn_h = self.row_h - 2 * self.pad
        self.disp_w = self.width - 2 * self.pad
        self.disp_h = self.row_h - 2 * self.pad
        self.line_h = max(self.FONT_H, self.disp_h // 2)
        # Font scale: ~1 at 320px, ~2 at 640px.
        self.font_scale = max(1, self.unit // 280)
        self.expr_scale = max(1, self.font_scale)
        self.num_scale = max(1, self.font_scale + (1 if self.unit >= 480 else 0))

        self.pal = get_palette(name="material_design")
        # Dark calculator theme (iPhone / Google style).
        self.bg = _c565(0x12, 0x12, 0x14)
        self.disp_bg = _c565(0x1C, 0x1C, 0x1E)
        self.digit_bg = _c565(0x33, 0x33, 0x38)
        self.fn_bg = _c565(0x55, 0x55, 0x5A)
        self.op_bg = _c565(0xFF, 0x9F, 0x0A)
        self.eq_bg = _c565(0x0A, 0x84, 0xFF)
        self.press_bg = _c565(0xFF, 0xFF, 0xFF)
        self.expr_fg = _c565(0xAE, 0xAE, 0xB2)
        self.num_fg = _c565(0xFF, 0xFF, 0xFF)
        self.err_fg = _c565(0xFF, 0x45, 0x3A)
        self.digit_fg = _c565(0xFF, 0xFF, 0xFF)
        self.fn_fg = _c565(0xFF, 0xFF, 0xFF)
        self.op_fg = _c565(0x1C, 0x1C, 0x1E)

        self.engine = CalcEngine()
        self.button_pos = {}
        self._label_for = {}

        keypad_keys = [None] * self.COLS + list(_CODES)
        self.keypad = Keypad(
            runtime,
            0,
            0,
            self.width,
            self.height,
            self.COLS,
            self.ROWS,
            keypad_keys,
        )

        # Scratch buffers sized for the largest button (double-wide on last row).
        max_btn_w = self.col_w * 2 - 2 * self.pad
        self.btn_ba = bytearray(max_btn_w * self.btn_h * self.bpp)
        self.btn_fb = FrameBuffer(self.btn_ba, max_btn_w, self.btn_h, RGB565)
        self.line_ba = bytearray(self.disp_w * self.line_h * self.bpp)
        self.line_fb = FrameBuffer(self.line_ba, self.disp_w, self.line_h, RGB565)

        self._draw_all()

    def _colors_for(self, label):
        if label in "0123456789.":
            return self.digit_fg, self.digit_bg
        if label in "+-*/":
            return self.op_fg, self.op_bg
        if label == "=":
            return self.digit_fg, self.eq_bg
        return self.fn_fg, self.fn_bg

    def _draw_all(self):
        display_drv.fill(self.bg)
        # Display band
        display_drv.fill_rect(
            self.pad,
            self.pad,
            self.disp_w,
            self.disp_h,
            self.disp_bg,
        )
        for i, (code, label) in enumerate(zip(_CODES, _LABELS)):
            col = i % self.COLS
            row = i // self.COLS + 1
            self.button_pos[code] = (col, row, label)
            self._label_for[code] = label
            # Skip the right half of a double-wide button (drawn with left cell).
            if label in ("sqrt", "%") and col in (1, 3):
                continue
            self._draw_button(col, row, label, pressed=False)
        self._refresh_display()
        display_drv.show()

    def _button_geom(self, col, row, label):
        x = col * self.col_w + self.pad
        y = row * self.row_h + self.pad
        w = self.btn_w
        h = self.btn_h
        if label in ("sqrt", "%"):
            w = self.col_w * 2 - 2 * self.pad
        return x, y, w, h

    def _draw_button(self, col, row, label, pressed=False):
        x, y, w, h = self._button_geom(col, row, label)
        fg, bg = self._colors_for(label)
        if pressed:
            fg, bg = self.bg, self.press_bg

        # Rebind framebuffer to this button's size.
        self.btn_fb = FrameBuffer(self.btn_ba, w, h, RGB565)
        self.btn_fb.fill(self.bg)
        r = min(self.radius, w // 4, h // 4)
        self.btn_fb.round_rect(0, 0, w, h, r, bg, True)

        text = "sqrt" if label == "sqrt" else label
        # Shrink scale if the label is wider than the button.
        scale = self.font_scale
        while scale > 1 and len(text) * self.FONT_W * scale > w - 2:
            scale -= 1
        tw = len(text) * self.FONT_W * scale
        th = self.FONT_H * scale
        tx = max(0, (w - tw) // 2)
        ty = max(0, (h - th) // 2)
        self.btn_fb.text16(text, tx, ty, fg, scale=scale)
        display_drv.blit_rect(self.btn_ba[: w * h * self.bpp], x, y, w, h)

    def _right_text(self, fb, text, scale, color, y_off):
        tw = len(text) * self.FONT_W * scale
        x = max(self.pad, self.disp_w - tw - self.pad)
        fb.text16(text, x, y_off, color, scale=scale)

    def _refresh_display(self):
        expr = self.engine.expression
        num = self.engine.display
        num_fg = self.err_fg if self.engine.is_error else self.num_fg

        # Expression (top half of display band)
        self.line_fb = FrameBuffer(self.line_ba, self.disp_w, self.line_h, RGB565)
        self.line_fb.fill(self.disp_bg)
        if expr:
            # Truncate from the left if too long.
            max_chars = max(4, (self.disp_w - 2 * self.pad) // (self.FONT_W * self.expr_scale))
            if len(expr) > max_chars:
                expr = "..." + expr[-(max_chars - 3) :]
            self._right_text(self.line_fb, expr, self.expr_scale, self.expr_fg, self.pad)
        display_drv.blit_rect(
            self.line_ba[: self.disp_w * self.line_h * self.bpp],
            self.pad,
            self.pad,
            self.disp_w,
            self.line_h,
        )

        # Main number (bottom half)
        self.line_fb.fill(self.disp_bg)
        max_chars = max(4, (self.disp_w - 2 * self.pad) // (self.FONT_W * self.num_scale))
        if len(num) > max_chars:
            num = num[-(max_chars):]
        y_off = max(0, (self.line_h - self.FONT_H * self.num_scale) // 2)
        self._right_text(self.line_fb, num, self.num_scale, num_fg, y_off)
        display_drv.blit_rect(
            self.line_ba[: self.disp_w * self.line_h * self.bpp],
            self.pad,
            self.pad + self.line_h,
            self.disp_w,
            self.line_h,
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
        codes = self.keypad.read()
        if not codes:
            return presses
        for code in codes:
            if code is None:
                continue
            label = self._label_for.get(code)
            if label is None:
                label = _KEY_ALIASES.get(code)
            if label is None and isinstance(code, int) and 48 <= code <= 57:
                label = chr(code)
            if label is None:
                continue
            info = self.button_pos.get(code)
            if info is not None:
                col, row, label = info
            else:
                # Keyboard alias without a grid cell — still feed the engine.
                self.engine.press(label)
                self._refresh_display()
                display_drv.show()
                continue
            # Map double-wide right-half taps to the left cell for drawing.
            if label == "sqrt" and col == 1:
                col = 0
            if label == "%" and col == 3:
                col = 2
            self._handle_press(col, row, label)
            presses.append((col, row, label))
        return presses

    def _handle_press(self, col, row, label):
        self._draw_button(col, row, label, pressed=True)
        self.engine.press(label)
        self._refresh_display()
        display_drv.show()

    def release_button(self, col, row, label):
        self._draw_button(col, row, label, pressed=False)
        display_drv.show()


def _sync_poll(calc):
    pending_release = None
    release_timer = Timer(-1)

    def release_button(_=None):
        nonlocal pending_release
        if pending_release is None:
            return
        col, row, label = pending_release
        pending_release = None
        calc.release_button(col, row, label)

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
    from multimer import asyncio

    calc = _Calculator()
    while True:
        if calc.poll_quit():
            break
        for press in calc.read_presses():
            await asyncio.sleep(0.15)
            calc.release_button(*press)
        await asyncio.sleep(0.02)


dual_main(main_sync, main_async, async_mode=runtime.timer_async)
