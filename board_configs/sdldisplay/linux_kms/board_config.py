# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
Linux KMS / DRM board config (no X11/Wayland window manager).

Why SDL_VIDEODRIVER=kmsdrm: bare framebuffer / HDMI scanout on Pi and similar
SBCs without a desktop — reuse SDLDisplay + usdl2 instead of a native fbdev path.
Must be set before SDL_Init (inside SDLDisplay).
"""

import sys

from displaysys import env_set

# Why: force SDL's KMS/DRM backend before SDLDisplay constructs the window.
env_set("SDL_VIDEODRIVER", "kmsdrm")

import usdl2
from displaysys.sdldisplay import SDLDisplay as DTDisplay
from displaysys.sdldisplay import get_events
import eventsys

# Why scale=1.0: KMS modes are typically already panel-native; avoid desktop
# letterboxing meant for small logical FBs on large monitors.
width = 320
height = 480
rotation = 0
scale = 1.0

# Why FULLSCREEN: under kmsdrm there is no window manager chrome; fullscreen
# matches the DRM mode instead of a floating window.
window_flags = usdl2.SDL_WINDOW_FULLSCREEN_DESKTOP | usdl2.SDL_WINDOW_ALLOW_HIGHDPI

display_drv = DTDisplay(
    width=width,
    height=height,
    rotation=rotation,
    title=f"{sys.implementation.name} on linux-kms",
    scale=scale,
    window_flags=window_flags,
)

runtime = eventsys.Runtime(display=display_drv, host_read=get_events)

display_drv.fill(0)
