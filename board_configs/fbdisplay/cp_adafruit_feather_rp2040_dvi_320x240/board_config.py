# SPDX-FileCopyrightText: 2026 Brad Barnett
# SPDX-License-Identifier: MIT
"""Adafruit Feather RP2040 DVI (320x240) — CircuitPython + LVGL POC.

Paint path mirrors ``cp_qualia_tl040hds20`` (Bitmap + TileGrid + ColorConverter).
Flush/tick wiring mirrors ``add_ons/display_driver.DisplayDriver`` inline — no
``display_driver`` import, no ``event_loop``, no input devices, no timers.

RP2040 SRAM is too tight for a full-screen RGB565 Bitmap beside the DVI
framebuffer, so LVGL paints 160x120 and ``Group(scale=2)`` upscales. On an
RP2350 this can grow toward native 320x240 (or higher) without the scale hack.
"""

import gc
import time

import bitmaptools
import board
import displayio
import framebufferio
import lvgl as lv
import picodvi

# DVI is 320x240 @ 8bpp. A full-screen RGB565 Bitmap (~150KB) will not fit in
# RP2040 SRAM beside the framebuffer, so LVGL paints a half-res surface and
# displayio Group(scale=2) upscales it.
WIDTH = 160
HEIGHT = 120
TICK_MS = 30

displayio.release_displays()
gc.collect()

fb = picodvi.Framebuffer(
    320,
    240,
    clk_dp=board.CKP,
    clk_dn=board.CKN,
    red_dp=board.D0P,
    red_dn=board.D0N,
    green_dp=board.D1P,
    green_dn=board.D1N,
    blue_dp=board.D2P,
    blue_dn=board.D2N,
    color_depth=8,
)
display = framebufferio.FramebufferDisplay(fb, auto_refresh=True)

_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 65535)
_tile = displayio.TileGrid(
    _bitmap,
    pixel_shader=displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565),
)
_group = displayio.Group(scale=2)
_group.append(_tile)
display.root_group = _group

gc.collect()
print("free after displayio:", gc.mem_free())


def _as_u16_pixels(buf):
    mv = memoryview(buf)
    try:
        return mv.cast("H")
    except (AttributeError, TypeError, ValueError):
        import array

        return array.array("H", mv)


def _flush_cb(disp_drv, area, color_p):
    w = area.x2 - area.x1 + 1
    h = area.y2 - area.y1 + 1
    data = color_p.__dereference__(w * h * 2)
    bitmaptools.arrayblit(
        _bitmap, _as_u16_pixels(data), area.x1, area.y1, area.x1 + w, area.y1 + h
    )
    lv_disp.flush_ready()


lv.init()
color_format = lv.COLOR_FORMAT.RGB565
_draw_buf1 = lv.draw_buf_create(WIDTH, HEIGHT // 10, color_format, 0)
_draw_buf2 = lv.draw_buf_create(WIDTH, HEIGHT // 10, color_format, 0)

lv_disp = lv.display_create(WIDTH, HEIGHT)
lv_disp.set_flush_cb(_flush_cb)
lv_disp.set_color_format(color_format)
lv_disp.set_draw_buffers(_draw_buf1, _draw_buf2)
lv_disp.set_render_mode(lv.DISPLAY_RENDER_MODE.PARTIAL)

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x101820), 0)

title = lv.label(scr)
title.set_text("LVGL on DVI")
title.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
title.align(lv.ALIGN.TOP_MID, 0, 8)

box = lv.obj(scr)
box.set_size(100, 40)
box.align(lv.ALIGN.CENTER, 0, 0)
box.set_style_bg_color(lv.color_hex(0xE91E63), 0)
box.set_style_border_width(0, 0)

lbl = lv.label(box)
lbl.set_text("hello")
lbl.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
lbl.center()

print("free after lvgl:", gc.mem_free())
print("LVGL+DVI POC running")

while True:
    lv.tick_inc(TICK_MS)
    lv.task_handler()
    time.sleep(TICK_MS / 1000)
