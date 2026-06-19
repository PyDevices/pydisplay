"""
lv_touch_test.py
Tests touchscreen and allows changing touch driver rotation
to find a rotation that matches the display rotation.
"""

import display_driver
import lvgl as lv


alignments = (
    (lv.ALIGN.TOP_LEFT, 0, 0),
    (lv.ALIGN.TOP_MID, 0, 0),
    (lv.ALIGN.TOP_RIGHT, 0, 0),
    (lv.ALIGN.LEFT_MID, 0, 0),
    (lv.ALIGN.CENTER, 0, 0),
    (lv.ALIGN.RIGHT_MID, 0, 0),
    (lv.ALIGN.BOTTOM_LEFT, 0, 0),
    (lv.ALIGN.BOTTOM_MID, 0, 0),
    (lv.ALIGN.BOTTOM_RIGHT, 0, 0),
)

style_default = lv.style_t()
style_default.init()
style_default.set_width(lv.pct(33))
style_default.set_height(lv.pct(33))
style_default.set_bg_color(lv.palette_main(lv.PALETTE.BLUE))

style_pressed = lv.style_t()
style_pressed.init()
style_pressed.set_transform_width(-10)
style_pressed.set_transform_height(-10)
style_pressed.set_bg_color(lv.palette_main(lv.PALETTE.GREEN))

style_focused = lv.style_t()
style_focused.init()
style_focused.set_bg_color(lv.palette_main(lv.PALETTE.RED))

parent = lv.screen_active()

i = 0
for alignment in alignments:
    i += 1
    btn = lv.button(parent)
    btn.align(*alignment)
    btn.add_style(style_default, 0)
    btn.add_style(style_pressed, lv.STATE.PRESSED)
    btn.add_style(style_focused, lv.STATE.FOCUSED)
    label = lv.label(btn)
    label.set_text(f"Btn{i}")
    label.center()
