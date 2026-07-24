# Board wrapper: eventsys_touch_coords + UDP NDJSON (session 4c370d).
# mpftp run this with --no-follow; tap the on-screen crosses.

import sys
import json
import socket

sys.path.insert(0, "/lib")
import path  # noqa: F401

from board_config import display_drv, runtime
import eventsys

_DBG = ("192.168.1.143", 41234)
_sock = None


def _udp(msg, **data):
    global _sock
    rec = {
        "sessionId": "4c370d",
        "runId": "touch-coords",
        "hypothesisId": "H40",
        "location": "dbg_touch_coords_udp.py",
        "message": msg,
        "data": data,
    }
    try:
        import time

        rec["timestamp"] = int(time.ticks_ms())
    except Exception:
        pass
    line = json.dumps(rec)
    print(line)
    try:
        if _sock is None:
            _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.sendto((line + "\n").encode(), _DBG)
    except Exception:
        pass


FG, BG, ARM = 0xFFFF, 0x0000, 12
W, H = display_drv.width, display_drv.height
TARGETS = (
    (W // 4, H // 4),
    (W // 2, H // 4),
    (3 * W // 4, H // 2),
    (W // 2, 3 * H // 4),
)

idx = 0
results = []
_busy = False

_udp("start", w=W, h=H, rot=display_drv.rotation, fb=str(type(getattr(display_drv, "_fb", None) or display_drv)))


def _plus(x, y, c):
    display_drv.fill_rect(x - ARM, y, 2 * ARM + 1, 1, c)
    display_drv.fill_rect(x, y - ARM, 1, 2 * ARM + 1, c)


def _show():
    display_drv.fill_rect(0, 0, W, H, BG)
    x, y = TARGETS[idx]
    _plus(x, y, FG)
    display_drv.show()
    _udp("target", i=idx + 1, n=len(TARGETS), x=x, y=y)


def _on_up(e):
    global idx, _busy
    if _busy or e.button != 1 or idx >= len(TARGETS):
        return
    _busy = True
    try:
        gx, gy = e.pos
        tx, ty = TARGETS[idx]
        err = (gx - tx, gy - ty)
        results.append(((tx, ty), (gx, gy), err))
        _udp("tap", i=idx + 1, got=(gx, gy), target=(tx, ty), err=err)
        idx += 1
        import time

        time.sleep_ms(400)
        if idx >= len(TARGETS):
            _udp("done", results=results)
            display_drv.fill_rect(0, 0, W, H, BG)
            display_drv.show()
        else:
            _show()
            time.sleep_ms(400)
    finally:
        _busy = False


touch = getattr(display_drv, "touch_device", None)
if touch is not None:
    touch.rotation_table = (0, 0, 0, 0)

# Ensure touch auto-service after any prior stop_timer in session.
arm = getattr(runtime, "_arm_service", None)
if callable(arm):
    arm()

_show()
runtime.on(eventsys.MOUSEBUTTONUP, _on_up)
_udp("armed", service=bool(getattr(runtime, "_service_subscription", None)))
runtime.run_forever()
# ESP32 interactive+signals: keep process alive
import multimer

while not getattr(runtime, "quit_requested", False):
    multimer.sleep_ms(100)
