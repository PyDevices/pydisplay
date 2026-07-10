# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
display_driver.py - LVGL driver configuration for pydisplay.  Requires a valid
board_config.py to be in a directory on the micropython path.
"""

import gc
import sys

from board_config import display_drv, runtime
import lv_utils
import lvgl as lv

import eventsys
from eventsys import events

_driver_ref = None


def main():
    global _driver_ref
    gc.collect()
    if not lv.is_initialized():
        lv.init()
    if not lv_utils.event_loop.is_running():
        if runtime is not None:
            runtime.claim_display_refresh()
        loop_inst = lv_utils.event_loop(
            asynchronous=runtime.timer_async if runtime is not None else False,
            refresh_cb=display_drv.show,
        )
    else:
        loop_inst = lv_utils.event_loop.current_instance()

    if loop_inst is not None:
        loop_inst.disable()
    try:
        if lv.group_get_default() is None:
            lv.group_create().set_default()

        devs = runtime.devices if runtime is not None else []
        _driver_ref = DisplayDriver(
            display_drv,
            devs,
        )
    finally:
        if loop_inst is not None:
            loop_inst.enable()

    if runtime is not None:

        def _lvgl_shutdown_before_quit():
            inst = lv_utils.event_loop.current_instance()
            if inst is not None:
                inst.deinit()

        runtime.before_quit = _lvgl_shutdown_before_quit


class _TouchState:
    x = 0
    y = 0
    pressed = False


def _touch_cb(event, indev, data):
    if event is not None:
        if event.type == events.MOUSEBUTTONDOWN and event.button == 1:
            _TouchState.x, _TouchState.y = event.pos
            _TouchState.pressed = True
        elif event.type == events.MOUSEMOTION and event.buttons[0]:
            _TouchState.x, _TouchState.y = event.pos
        elif event.type == events.MOUSEBUTTONUP and event.button == 1:
            _TouchState.x, _TouchState.y = event.pos
            _TouchState.pressed = False
    data.point = lv.point_t({"x": _TouchState.x, "y": _TouchState.y})
    data.state = lv.INDEV_STATE.PRESSED if _TouchState.pressed else lv.INDEV_STATE.RELEASED


def _encoder_cb(event, indev, data):
    if event is None:
        return
    if event.type == events.MOUSEWHEEL:
        data.enc_diff = event.x if event.flipped is False else -event.x
    elif event.type == events.MOUSEBUTTONDOWN and event.button == 3:
        data.state = lv.INDEV_STATE.PRESSED
    elif event.type == events.MOUSEBUTTONUP and event.button == 3:
        data.state = lv.INDEV_STATE.RELEASED


def _keypad_cb(event, indev, data):
    if event is None:
        return
    if event.type == events.KEYDOWN:
        data.state = lv.INDEV_STATE.PRESSED
        data.key = event.key
    elif event.type == events.KEYUP:
        data.state = lv.INDEV_STATE.RELEASED
        data.key = event.key


def create_devices(devs, lv_display):
    for device in devs:
        if device.type in (eventsys.TOUCH, eventsys.ENCODER, eventsys.KEYPAD):
            indev = lv.indev_create()
            indev.set_display(lv_display)
            device.user_data = indev
            if device.type == eventsys.TOUCH:
                device.subscribe(_touch_cb)
                indev.set_type(lv.INDEV_TYPE.POINTER)
            elif device.type == eventsys.ENCODER:
                device.subscribe(_encoder_cb)
                indev.set_type(lv.INDEV_TYPE.ENCODER)
            elif device.type == eventsys.KEYPAD:
                device.subscribe(_keypad_cb)
                indev.set_type(lv.INDEV_TYPE.KEYPAD)
            indev.set_group(lv.group_get_default())
            indev.set_read_cb(device.poll)
        elif device.type == eventsys.HOST:
            vd = eventsys.VirtualDevices(device)
            create_devices(vd.devices, lv_display)


class DisplayDriver:
    def __init__(
        self,
        display_drv,
        devs=None,
        color_format=lv.COLOR_FORMAT.RGB565,
        blocking=True,
    ):
        if devs is None:
            devs = []
        gc.collect()
        if display_drv.requires_byteswap:
            self._needs_swap = display_drv.disable_auto_byteswap(True)
        else:
            self._needs_swap = False
        self._color_size = lv.color_format_get_size(color_format)
        self._blocking = blocking

        self._draw_buf1 = lv.draw_buf_create(
            display_drv.width, display_drv.height // 10, color_format, 0
        )
        self._draw_buf2 = lv.draw_buf_create(
            display_drv.width, display_drv.height // 10, color_format, 0
        )

        self.lv_display = lv.display_create(display_drv.width, display_drv.height)
        self.lv_display.set_flush_cb(self._flush_cb)
        self.lv_display.set_color_format(color_format)
        if not self._blocking:
            display_drv.display_bus.register_callback(self.lv_display.flush_ready)
        self.lv_display.set_draw_buffers(self._draw_buf1, self._draw_buf2)
        self.lv_display.set_render_mode(lv.DISPLAY_RENDER_MODE.PARTIAL)
        create_devices(devs, self.lv_display)

    def _flush_cb(self, disp_drv, area, color_p):
        if hasattr(display_drv, "_sdl_active") and not display_drv._sdl_active():
            self.lv_display.flush_ready()
            return
        width = area.x2 - area.x1 + 1
        height = area.y2 - area.y1 + 1

        if self._needs_swap:
            lv.draw_sw_rgb565_swap(color_p, width * height)

        data = color_p.__dereference__(width * height * self._color_size)
        display_drv.blit_rect(data, area.x1, area.y1, width, height)
        if self._blocking:
            self.lv_display.flush_ready()


def run():
    from multimer import sleep_ms

    inst = lv_utils.event_loop.current_instance()
    if inst is not None:
        if sys.platform == "darwin":
            inst.run()
            return
        if sys.platform != "win32":
            return

    loop_i = 0
    while True:
        sleep_ms(1)
        loop_i += 1
        if runtime is not None and (loop_i & 3) == 0:
            runtime.poll()
        if runtime is not None and runtime.quit_requested:
            return
        if getattr(display_drv, "_deinitialized", False):
            return


main()
