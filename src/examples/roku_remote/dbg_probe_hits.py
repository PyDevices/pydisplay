# Lean on-device probe: sector hits + page-cache timings (no ECP socket waits).
import gc
import os
import sys
import time

sys.path.insert(0, "/lib")
sys.path.insert(0, "/lib/roku_remote")

try:
    os.remove("/dbg_roku.ndjson")
except Exception:
    pass

import path  # noqa: F401
import roku_engine

roku_engine._LAUNCHER_OWNS_RUN = True
from board_config import display_drv, runtime
import display_driver as dd  # noqa: F401
import lvgl as lv
import roku_lvgl as rl

print("PROBE_START", display_drv.width, display_drv.height)


def _pump(n=4):
    for _ in range(n):
        try:
            lv.task_handler()
        except Exception:
            pass
        time.sleep_ms(30)


def _resolve(ui, x, y):
    hits = getattr(ui, "_remote_hits", None) or []
    dpad = getattr(ui, "_remote_dpad", None)
    key = None
    via = None
    if dpad is not None:
        x1, y1, x2, y2 = dpad
        if x1 <= x <= x2 and y1 <= y <= y2:
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            dx = x - cx
            dy = y - cy
            rw = max(1, x2 - x1 + 1)
            ok_r = max(8, rw // 6)
            if dx * dx + dy * dy <= ok_r * ok_r:
                key = "Select"
            elif abs(dy) >= abs(dx):
                key = "Up" if dy < 0 else "Down"
            else:
                key = "Left" if dx < 0 else "Right"
            via = "dpad"
    if key is None:
        for x1, y1, x2, y2, action in hits:
            if x1 <= x <= x2 and y1 <= y <= y2:
                key = action if isinstance(action, str) else "fn"
                via = "rect"
                break
    return key, via, dpad, len(hits)


runtime.stop_timer()
time.sleep_ms(50)
gc.collect()

ui = rl.create(start_page="devices")
_pump(4)
print("PROBE_DEVICES_OK")

devs = ui.discover_list or []
if not devs:
    try:
        ui.discover_list = ui._merge_device_lists(ui.engine.cached_devices() or [], [])
        devs = ui.discover_list or []
    except Exception:
        pass

# Build remote without network connect path when possible.
if devs:
    try:
        ui.engine.host = (devs[0].get("host") or "").strip()
    except Exception:
        pass
ui._show_page("remote")
_pump(6)
print("PROBE_REMOTE", ui.page, getattr(ui, "_remote_dpad", None), len(getattr(ui, "_remote_hits", None) or []))

dpad = getattr(ui, "_remote_dpad", None)
if dpad:
    x1, y1, x2, y2 = dpad
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    rw = x2 - x1 + 1
    samples = [
        ("ok", cx, cy),
        ("up", cx, cy - rw // 3),
        ("down", cx, cy + rw // 3),
        ("left", cx - rw // 3, cy),
        ("right", cx + rw // 3, cy),
        ("mid_ring_up", cx, y1 + (cy - y1) // 2),
        ("mid_up_left", cx - rw // 5, cy - rw // 5),
    ]
    for name, x, y in samples:
        key, via, _, n = _resolve(ui, x, y)
        print("PROBE_HIT", name, key, via, x, y, "n", n)
        # Exercise queue path only (no socket): append + drain with stub host skip
        if isinstance(key, str):
            # Use engine.press only if host set; still wait=False / short
            ui._ecp_q.append(key)
    # Do not drain ECP (would block on WiFi). Just report queue depth.
    print("PROBE_ECP_Q", len(getattr(ui, "_ecp_q", []) or []))

# Page cache timings
times = {}
for label, page in (("more", "more"), ("remote2", "remote"), ("apps", "apps"), ("remote3", "remote")):
    t0 = time.ticks_ms()
    ui._show_page(page)
    _pump(3)
    times[label] = int(time.ticks_diff(time.ticks_ms(), t0))
print("PROBE_PAGE_TIMES", times)
print("PROBE_AFTER", ui.page, getattr(ui, "_remote_dpad", None), len(getattr(ui, "_remote_hits", None) or []))

if getattr(ui, "_remote_dpad", None):
    x1, y1, x2, y2 = ui._remote_dpad
    key, via, _, _ = _resolve(ui, (x1 + x2) // 2, (y1 + y2) // 2)
    print("PROBE_HIT_AFTER_CACHE", key, via)

print("PROBE_DONE")
try:
    runtime.stop_timer()
except Exception:
    pass
