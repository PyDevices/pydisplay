# deps: lvgl
# modules: roku_engine, roku_lvgl
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
roku_remote
====================================================
Launcher for the flagship museum-quality LVGL Roku remote.

The Roku remote is now a modular stack sharing one UI-agnostic engine:

* :mod:`roku_engine`   -- ECP client + discovery + label/action helpers (no UI)
* :mod:`roku_lvgl`     -- flagship LVGL front end (**launched here**)
* :mod:`roku_graphics` -- ``graphics.FrameBuffer`` front end
* :mod:`roku_widgets`  -- ``pdwidgets`` front end

Running ``roku_remote`` opens the LVGL UI. To try another front end, run
``roku_graphics`` or ``roku_widgets`` directly. Requires Roku
**Control by mobile apps -> Enabled**; join WiFi before running on a
microcontroller. Set the target with ``ROKU_HOST`` in :mod:`roku_engine`, or
use SCAN / the IP pad on device.
"""

import sys

_EXAMPLES = __file__.replace("\\", "/").rsplit("/", 1)[0]
if _EXAMPLES not in sys.path:
    sys.path.insert(0, _EXAMPLES)

# Importing the LVGL front end builds the UI and hands control to
# ``runtime.run_forever()``; nothing else to do here.
import roku_lvgl  # noqa: F401,E402
