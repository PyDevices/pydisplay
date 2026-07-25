#!/usr/bin/env python3
"""Probe whether SDL delivers real multitouch (SDL_FINGER*) vs mouse-only.

Run from ``pydisplay/src``::

    python ../tools/sdl_touch_probe.py

Touch the window with 1-2 fingers (or a touchscreen stylus). Trackpad
OS-level pinch usually never appears here. Quit: Esc or close window.

Under WSL/WSLg, multitouch often never reaches SDL - try Windows
``python.exe`` from the same tree if this only prints MOUSE*.
"""

from __future__ import annotations

import os
import sys
import time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

os.chdir(_SRC)

import usdl2  # noqa: E402

from displaysys.sdldisplay import SDLDisplay, get_events  # noqa: E402
from eventsys import events  # noqa: E402
import lib.path  # noqa: E402, F401

_HEARTBEAT_S = 0.5


def main():
    w, h = 480, 320
    disp = SDLDisplay(width=w, height=h, rotation=0, title="SDL touch probe", scale=1)
    disp.fill(0)
    print("SDL touch probe - touch the window; watch for FINGER* lines.")
    print("MOUSE* only = no app multitouch (WSL/trackpad pinch is normal).")
    print("Ctrl+C or close window to quit.\n")

    counts = {"mouse": 0, "finger": 0, "other": 0}
    max_fingers = 0
    fingers = {}
    t0 = time.time()
    try:
        while True:
            batch = get_events()
            if not batch:
                time.sleep(0.01)
                continue
            for e in batch:
                if e.type == events.QUIT:
                    return
                if e.type in (events.FINGERDOWN, events.FINGERMOTION, events.FINGERUP):
                    counts["finger"] += 1
                    if e.type == events.FINGERUP:
                        fingers.pop(e.finger_id, None)
                    else:
                        fingers[e.finger_id] = e.pos
                    max_fingers = max(max_fingers, len(fingers))
                    name = {
                        events.FINGERDOWN: "FINGERDOWN",
                        events.FINGERMOTION: "FINGERMOTION",
                        events.FINGERUP: "FINGERUP",
                    }[e.type]
                    print(
                        f"{name:14} id={e.finger_id} pos={e.pos} "
                        f"active={len(fingers)} max={max_fingers}"
                    )
                elif e.type in (
                    events.MOUSEMOTION,
                    events.MOUSEBUTTONDOWN,
                    events.MOUSEBUTTONUP,
                ):
                    counts["mouse"] += 1
                    touch = getattr(e, "touch", False)
                    if e.type != events.MOUSEMOTION or getattr(e, "buttons", (0,))[0]:
                        print(f"{'MOUSE':14} type={e.type:#x} pos={e.pos} touch_flag={touch}")
                else:
                    counts["other"] += 1
            if time.time() - t0 > _HEARTBEAT_S:
                # heartbeat so a quiet session is obvious
                t0 = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        print(
            f"\nsummary: finger_events={counts['finger']} "
            f"mouse_events={counts['mouse']} max_simultaneous={max_fingers}"
        )
        try:
            disp.deinit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
