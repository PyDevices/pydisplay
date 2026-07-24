# Board launcher that honors /roku_prefs ``frontend`` (lvgl|widgets|graphics).
# Does not force desktop PYDISPLAY_WIDTH/HEIGHT (unlike roku_remote.py).
#
#   import dbg_s3_frontend
# or: mpftp run …/dbg_s3_frontend.py

import sys
import os
import time
import gc
import json
import socket

sys.path.insert(0, "/lib")
sys.path.insert(0, "/lib/roku_remote")

_DBG_UDP = ("192.168.1.143", 41234)
_dbg_sock = None


def _stage(msg, **data):
    global _dbg_sock
    rec = {
        "sessionId": "4c370d",
        "runId": "frontend-ab",
        "hypothesisId": "H30",
        "location": "dbg_s3_frontend.py",
        "message": msg,
        "data": data,
        "timestamp": int(time.ticks_ms() if hasattr(time, "ticks_ms") else time.time() * 1000),
    }
    line = json.dumps(rec)
    try:
        print(line)
    except Exception:
        pass
    try:
        if _dbg_sock is None:
            _dbg_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _dbg_sock.sendto((line + "\n").encode(), _DBG_UDP)
    except Exception:
        pass


_stage("S0")
import path  # noqa: F401

try:
    os.remove("/dbg_roku.ndjson")
except Exception:
    pass

import roku_engine

roku_engine._LAUNCHER_OWNS_RUN = True
fe = roku_engine.get_frontend()
_stage("S1_prefs", frontend=fe)

from board_config import display_drv, runtime

_stage("S2", rot=display_drv.rotation, w=display_drv.width, h=display_drv.height)
# Drop board_config's display auto-refresh before the front end owns ticks.
# Must re-arm Runtime._service_tick afterward or touch never polls (widgets
# path had no display_driver to restore it — H31).
runtime.stop_timer()
time.sleep_ms(200)
gc.collect()

if fe == "widgets":
    import roku_widgets as mod
elif fe == "graphics":
    import roku_graphics as mod
else:
    import display_driver as dd  # noqa: F401 — LVGL path

    _stage(
        "S3_lvgl",
        sw_rotate=getattr(dd._driver_ref, "_sw_rotate", None),
    )
    import roku_lvgl as mod

_stage("S4_import", frontend=fe, mod=getattr(mod, "FRONTEND", fe))
t0 = time.ticks_ms()
ui = mod.create(start_page="devices")
globals()["UI"] = ui
try:
    import builtins

    builtins.UI = ui
except Exception:
    pass
# Belt-and-suspenders if an older pdwidgets Display is on the board.
arm = getattr(runtime, "_arm_service", None)
svc = getattr(runtime, "_service_subscription", None)
if callable(arm) and svc is None:
    arm()
_stage(
    "S5_created",
    frontend=fe,
    ms=int(time.ticks_diff(time.ticks_ms(), t0)),
    ui=str(type(ui)),
    service=bool(getattr(runtime, "_service_subscription", None)),
    app_poll=bool(getattr(runtime, "_app_drives_poll", False)),
    claim=bool(getattr(runtime, "_refresh_claim", None)),
)

# #region agent log
def _dbg_touch_ev(event):
    try:
        _stage(
            "touch_ev",
            typ=int(getattr(event, "type", -1)),
            pos=getattr(event, "pos", None),
            app_poll=bool(getattr(runtime, "_app_drives_poll", False)),
        )
    except Exception:
        pass


try:
    from eventsys import events as _ev

    runtime.subscribe(
        _dbg_touch_ev,
        event_types=[_ev.MOUSEBUTTONDOWN, _ev.MOUSEBUTTONUP, _ev.MOUSEMOTION],
    )
    _stage("touch_sub_ok")
except Exception as e:
    _stage("touch_sub_fail", err=str(e))
# #endregion

runtime.run_forever()
_stage("keep_alive", frontend=fe, quit=bool(getattr(runtime, "quit_requested", False)))
import multimer

_n = 0
while not getattr(runtime, "quit_requested", False):
    multimer.sleep_ms(100)
    _n += 1
    # #region agent log
    # Sample raw GT911 every ~1s — never call runtime.poll() here (that sets
    # _app_drives_poll and permanently disables auto-service).
    if _n % 10 == 0:
        raw = None
        try:
            from board_config import touch_read_func as _tr

            raw = _tr()
        except Exception as e:
            raw = "err:%s" % e
        if raw is not None:
            _stage(
                "touch_raw",
                raw=list(raw) if isinstance(raw, tuple) else raw,
                app_poll=bool(getattr(runtime, "_app_drives_poll", False)),
                service=bool(getattr(runtime, "_service_subscription", None)),
            )
    # #endregion
_stage("ready")
