# SPDX-License-Identifier: MIT
"""
car_cluster soak worker (MicroPython / CPython).

Builds the cluster UI, injects keyboard events on a timer, writes heartbeats,
and exits cleanly after ``SOAK_SECONDS`` (default 300).

Does not use ``micropython -i`` — the parent harness covers interactive REPL
smoke separately. This process uses the paced ``run_forever`` sleep loop.
"""

import sys
import time

try:
    import uos as os
except ImportError:
    import os

# Resolve paths without os.path (MicroPython unix has a minimal ``os``).
_HERE = "/".join(__file__.replace("\\", "/").split("/")[:-1])
_ROOT = "/".join(_HERE.split("/")[:-1])
_SRC = _ROOT + "/src"
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
_PKG = _SRC + "/examples/car_cluster"
if _PKG not in sys.path:
    sys.path.insert(0, _PKG)

import input_map  # noqa: E402

import lib.path  # noqa: E402, F401

input_map.capture_virtual_devices()

from displaysys import env_get, env_set  # noqa: E402

if env_get("PYDISPLAY_WIDTH") is None:
    env_set("PYDISPLAY_WIDTH", "1200")
if env_get("PYDISPLAY_HEIGHT") is None:
    env_set("PYDISPLAY_HEIGHT", "560")
if env_get("PYDISPLAY_SCALE") is None:
    env_set("PYDISPLAY_SCALE", "1")


# Prefer env; fall back to displaysys for hosts without os.environ.
def _getenv(name, default=None):
    try:
        v = os.environ.get(name)
        if v is not None:
            return v
    except Exception:
        pass
    try:
        v = env_get(name)
        if v is not None:
            return v
    except Exception:
        pass
    return default


def _env_int(name, default):
    v = _getenv(name)
    if v is None:
        return default
    try:
        return int(v)
    except Exception:
        return default


SOAK_SECONDS = _env_int("SOAK_SECONDS", 300)
HEARTBEAT_PATH = _getenv("SOAK_HEARTBEAT", "/tmp/car_cluster_soak_hb")
RUN_ID = _getenv("SOAK_RUN_ID", "0")

from board_config import runtime  # noqa: E402
import display_driver  # noqa: E402
import focus_nav  # noqa: E402
import input_map as imap  # noqa: E402
import layout  # noqa: E402
import lvgl as lv  # noqa: E402
from vehicle import Vehicle  # noqa: E402

from eventsys import events  # noqa: E402
from eventsys.keys import Keys  # noqa: E402

try:
    from multimer import sleep_ms, ticks_diff, ticks_ms
except ImportError:

    def ticks_ms():
        return int(time.time() * 1000)

    def ticks_diff(a, b):
        return a - b

    def sleep_ms(ms):
        time.sleep(ms / 1000.0)


_KEY_CYCLE = (
    Keys.K_RIGHT,
    Keys.K_DOWN,
    Keys.K_RETURN,
    Keys.K_3,
    Keys.K_LEFT,
    Keys.K_UP,
    Keys.K_5,
    Keys.K_RIGHT,
    Keys.K_RETURN,
    Keys.K_1,
)


def _queue_device():
    import eventsys

    for dev in runtime.devices:
        if dev.type == eventsys.HOST:
            return dev
    return None


def _write_hb(note="ok"):
    try:
        with open(HEARTBEAT_PATH, "w") as f:
            f.write("%s %s %d %s\n" % (RUN_ID, note, ticks_ms(), note))
    except Exception:
        pass


def _inject_key(key):
    """Push key events onto the LVGL keypad fifo (no HOST._read monkeypatch).

    Monkeypatching HOST._read races the 10 ms display_driver host pump and
    wedged the soak after ~30 s / ~50 injects.
    """
    dd = sys.modules.get("display_driver")
    ref = getattr(dd, "_driver_ref", None) if dd is not None else None
    if ref is None:
        return False
    down = events.Key(events.KEYDOWN, None, key, 0, 0, 0)
    up = events.Key(events.KEYUP, None, key, 0, 0, 0)
    n = 0
    for vd in ref.virtual_devices:
        kp = getattr(vd, "_vd_keypad", None)
        if kp is None:
            continue
        kp.add_event(down)
        kp.add_event(up)
        n += 1
    return n > 0


def main():
    print("SOAK_START run=%s seconds=%d" % (RUN_ID, SOAK_SECONDS))
    _write_hb("start")

    inst = display_driver.event_loop.current_instance()
    if inst is not None:
        inst.disable()
    try:
        vehicle = Vehicle()
        nav = focus_nav.FocusNav()
        bridge = imap.InputBridge(runtime, vehicle, focus_nav=nav)
        bridge.install()
        ui = layout.ClusterUI(vehicle, focus_nav=nav)
        nav.set_active(focus_nav.FocusNav.LEFT)
        last_ms = ticks_ms()

        def on_vehicle(_t):
            nonlocal last_ms
            now = ticks_ms()
            dt = ticks_diff(now, last_ms) / 1000.0
            last_ms = now
            if dt < 0:
                dt = 0.05
            dt = min(dt, 0.25)
            vehicle.tick(dt)
            ui.update()

        lv.timer_create(on_vehicle, 40, None)

        def _drain_rails(_t):
            if ui.rails is not None:
                ui.rails.drain_pending()

        runtime.on_tick(_drain_rails, period=30, async_=False)
        ui.rails.drain_pending()
    finally:
        if inst is not None:
            inst.enable()

    key_i = [0]
    injects = [0]
    last_hb = [ticks_ms()]
    last_inject = [ticks_ms()]

    def on_soak(_t):
        now = ticks_ms()
        if ticks_diff(now, last_hb[0]) >= 1000:
            last_hb[0] = now
            _write_hb("beat injects=%d" % injects[0])
            print("SOAK_HB run=%s t=%d injects=%d" % (RUN_ID, now, injects[0]))
        if ticks_diff(now, last_inject[0]) >= 500:
            last_inject[0] = now
            key = _KEY_CYCLE[key_i[0] % len(_KEY_CYCLE)]
            key_i[0] += 1
            if _inject_key(key):
                injects[0] += 1

    runtime.on_tick(on_soak, period=100, async_=False)

    # Block with paced sleep (same as non-interactive run_forever).
    deadline = ticks_ms() + (SOAK_SECONDS * 1000)
    try:
        while ticks_diff(deadline, ticks_ms()) > 0 and not runtime.quit_requested:
            sleep_ms(50)
    finally:
        _write_hb("done injects=%d" % injects[0])
        print("SOAK_DONE run=%s injects=%d" % (RUN_ID, injects[0]))
        try:
            runtime.request_quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
