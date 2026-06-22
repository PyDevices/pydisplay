# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
SDL2 subset via the native usdl2 module (MicroPython and CircuitPython unix ports).
"""

import struct

import usdl2

from ._constants import *  # noqa: F403


def _window_title(title):
    if isinstance(title, (bytes, bytearray, memoryview)):
        return bytes(title).decode()
    return title


def SDL_Rect(x=0, y=0, w=0, h=0):
    return usdl2.rect(x, y, w, h)


def SDL_Point(x=0, y=0):
    return struct.pack("ii", x, y)


SDL_Init = usdl2.init
SDL_Quit = usdl2.quit
SDL_GetError = usdl2.get_error
SDL_PollEvent = usdl2.poll_event
SDL_GetKeyName = usdl2.get_key_name


def SDL_CreateWindow(title, x, y, w, h, flags):
    return usdl2.create_window(_window_title(title), x, y, w, h, flags)


SDL_DestroyWindow = usdl2.destroy_window
SDL_SetWindowSize = usdl2.set_window_size
SDL_CreateRenderer = usdl2.create_renderer
SDL_DestroyRenderer = usdl2.destroy_renderer
SDL_SetRenderDrawColor = usdl2.set_render_draw_color
SDL_SetRenderTarget = usdl2.set_render_target
SDL_RenderClear = usdl2.render_clear
SDL_RenderCopy = usdl2.render_copy
SDL_RenderCopyEx = usdl2.render_copyex
SDL_RenderPresent = usdl2.render_present
SDL_RenderFillRect = usdl2.render_fill_rect
SDL_RenderSetLogicalSize = usdl2.render_set_logical_size
SDL_CreateTexture = usdl2.create_texture
SDL_DestroyTexture = usdl2.destroy_texture
SDL_SetTextureBlendMode = usdl2.set_texture_blend_mode
SDL_UpdateTexture = usdl2.update_texture


def SDL_Event(event=None):
    if event is None:
        return usdl2.Event()
    try:
        if isinstance(event, usdl2.Event):
            return event
    except AttributeError:
        pass
    return usdl2.Event(event)
