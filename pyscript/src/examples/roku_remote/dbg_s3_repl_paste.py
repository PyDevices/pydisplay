# mpftp REPL paste mode corrupts multi-line pastes. Do not paste this file.
# Script is already on the board. After hard-reset, in the REPL:
#
#   import run_dbg
#
# (or: import dbg_s3_repl_paste)
#
# After UI / Ctrl-C:
#
#   print(open("/dbg_roku.ndjson").read())

import sys
import os
import time
import gc
import json
import socket

sys.path.insert(0, "/lib")
sys.path.insert(0, "/lib/roku_remote")

# #region agent log
_DBG_UDP = ("192.168.1.143", 41234)
_dbg_sock = None


def _stage(msg, **data):
    """UDP + print breadcrumb so launch progress is visible without CDC tee."""
    global _dbg_sock
    rec = {
        "sessionId": "4c370d",
        "runId": "launch",
        "hypothesisId": "H5",
        "location": "dbg_s3_repl_paste.py",
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
    except Exception as e:
        try:
            print("udp_fail", e)
        except Exception:
            pass


# #endregion

_stage("S0")
import path

try:
    os.remove("/dbg_roku.ndjson")
except Exception:
    pass
_stage("S1")
import roku_engine

roku_engine._LAUNCHER_OWNS_RUN = True
_stage("S2")
from board_config import display_drv, runtime

_stage("S3", rot=display_drv.rotation, w=display_drv.width, h=display_drv.height)
runtime.stop_timer()
time.sleep_ms(200)
gc.collect()
_stage("S4")
import display_driver as dd

_stage(
    "S5",
    sw_rotate=getattr(dd._driver_ref, "_sw_rotate", None),
    lv_w=dd._driver_ref.lv_display.get_horizontal_resolution(),
    lv_h=dd._driver_ref.lv_display.get_vertical_resolution(),
)
_stage("S6")
import roku_lvgl as rl
from roku_engine import get_ui_pref

_stage(
    "S7",
    shadows=get_ui_pref("ui_shadows"),
    gradients=get_ui_pref("ui_gradients"),
    progress=get_ui_pref("show_progress"),
    poll=get_ui_pref("playback_poll_s"),
)
_stage("S8_create")
# Select first — no host yet; avoids building Remote then tearing it down.
ui = rl.create(start_page="devices")
# Keep UI rooted across early run_forever return (interactive + machine.Timer).
globals()["UI"] = ui
try:
    import builtins

    builtins.UI = ui
except Exception:
    pass
_stage("S9_created", ui=str(type(ui)))
runtime.run_forever()
# #region agent log
# On ESP32, run_forever() often returns immediately (interactive + soft timer).
# mpftp run --no-follow still needs a live frame so GC does not collect UI and
# so the process does not fall back to a dead REPL before taps are captured.
_stage("keep_alive", quit=bool(getattr(runtime, "quit_requested", False)))
import multimer

while not getattr(runtime, "quit_requested", False):
    multimer.sleep_ms(100)
_stage("ready")
# #endregion
