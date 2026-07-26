# SPDX-FileCopyrightText: 2024 Brad Barnett
# SPDX-FileCopyrightText: 2021 Amir Gonnen (event_loop; MIT)
#
# SPDX-License-Identifier: MIT

"""
display_driver.py - LVGL display/input wiring and event loop for pydisplay.

Requires a valid board_config.py on the path. Importing this module initializes
LVGL, starts the shared ``event_loop`` (tick via ``runtime.on_tick``), and
registers display flush + input devices.

``event_loop`` was adapted from upstream lv_utils (Amir Gonnen). pydisplay
changes kept intentionally small:

* Periodic tick from ``eventsys.Runtime.on_tick`` instead of ``machine.Timer``.
* ``asyncio`` from ``multimer``.
* Sync path runs ``lv.task_handler()`` from the tick callback (re-entrancy
  guarded); the runtime timer already delivers on the main thread.
* Async mode arms the refresh task lazily on the first timer tick so module-top
  ``import display_driver`` is safe before any event loop exists.
* No app-loop helper — LVGL apps call ``runtime.run_forever()``.

Interactive desktop (librt + REPL): LVGL task handling is paced at ~30 ms with
a wall-clock gate. The Runtime timer stays at 10 ms; a host-pump subscription
drains SDL/keys every tick so the window cannot stall while LVGL is paused or
slow.
"""

import gc
import sys

from board_config import display_drv, runtime

# board_config.Runtime arms machine.Timer immediately. Halt it before any
# LVGL import/init: a soft-timer callback during lv_init / module load has
# corrupted draw_buf handlers on ESP32-P4 (Illegal instruction in
# width_to_stride). main() re-arms after DisplayDriver exists.
if runtime is not None:
    runtime.stop_timer()

import lvgl as lv

import eventsys
from eventsys import events

try:
    from multimer import asyncio, ticks_add, ticks_diff, ticks_ms
except ImportError:
    asyncio = None
    ticks_add = None
    ticks_diff = None
    ticks_ms = None

asyncio_available = asyncio is not None

LVGL_PERIOD_MS = 30
_driver_ref = None
_host_pump_sub = None


def _asyncio_loop_running():
    """True when an asyncio loop is already running (host loop or inside a task)."""
    if asyncio is None:
        return False
    if hasattr(asyncio, "get_running_loop"):
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    return False


class event_loop:
    """LVGL task loop driven by ``eventsys.Runtime.on_tick``.

    One instance may be active at a time. Sync mode runs ``lv.task_handler``
    from the shared timer; async mode signals an asyncio refresh task.
    Prefer ``import display_driver`` (module ``main()``) over constructing this
    by hand unless you need custom ``freq`` / ``asynchronous`` settings.
    """

    _current_instance = None

    def __init__(
        self,
        freq=None,
        max_scheduled=2,
        refresh_cb=None,
        asynchronous=False,
        exception_sink=None,
        period_ms=None,
    ):
        """Create and register the LVGL event loop.

        Args:
            freq: Desired Hz when ``period_ms`` is omitted (period = ``1000 // freq``).
            max_scheduled: Kept for lv_utils API parity (unused).
            refresh_cb: Optional zero-arg callable after each successful
                ``lv.task_handler()``.
            asynchronous: When True, drive LVGL via an asyncio refresh task.
            exception_sink: Callable receiving exceptions from task handling;
                defaults to :meth:`default_exception_sink`.
            period_ms: Explicit tick period in milliseconds (overrides ``freq``).

        Raises:
            RuntimeError: Another loop is already running, ``runtime`` is
                missing, or async mode is requested without asyncio.
        """
        if self.is_running():
            raise RuntimeError("Event loop is already running!")

        if not lv.is_initialized():
            lv.init()

        event_loop._current_instance = self

        if period_ms is not None:
            self.delay = int(period_ms)
        elif freq is not None:
            self.delay = max(1, 1000 // int(freq))
        else:
            self.delay = LVGL_PERIOD_MS

        self.refresh_cb = refresh_cb
        self.exception_sink = exception_sink if exception_sink else self.default_exception_sink
        # Start paused and do not arm machine.Timer until ``enable()``. On
        # ESP32-P4, even a no-op timer callback interrupting SPIRAM
        # ``draw_buf_create`` corrupts LVGL handlers (Illegal instruction,
        # MTVAL often an ASCII fragment like ``star``).
        self._pause = 1
        self._in_task = False
        self._next_ok_ms = None
        self._last_tick_ms = None

        self.asynchronous = asynchronous
        self.refresh_task = None
        self._timer_sub = None
        self._async_armed = False

        if runtime is None:
            raise RuntimeError("LVGL requires board_config.runtime")

        if self.asynchronous:
            if not asyncio_available:
                raise RuntimeError("Cannot run asynchronous event loop. asyncio is not available!")
            self.refresh_event = asyncio.Event()
            if _asyncio_loop_running():
                self.arm()
        # Sync: defer ``on_tick`` until first ``enable()`` (see ``_arm_sync_timer``).

    def _arm_sync_timer(self):
        """Subscribe the sync tick once; safe to call repeatedly."""
        if self.asynchronous:
            return
        # runtime.stop_timer() deinits the HW timer and clears callbacks but
        # does not notify us — drop a stale handle so we can re-subscribe.
        if self._timer_sub is not None:
            if runtime is not None and runtime._timer is not None:
                return
            self._timer_sub = None
        self._timer_sub = runtime.on_tick(self.timer_cb, period=self.delay, async_=False)

    def arm(self):
        """Create the async refresh task + shared timer once a loop is running.

        No-op in sync mode or when already armed. Safe to call repeatedly.
        """
        if not self.asynchronous or self._async_armed:
            return
        self._async_armed = True
        self.refresh_task = asyncio.create_task(self.async_refresh())
        self._timer_sub = runtime.on_tick(self.timer_cb, period=self.delay, async_=True)

    def deinit(self):
        """Stop the tick subscription / async task and clear the singleton."""
        if getattr(self, "_timer_sub", None) is not None:
            self._timer_sub.deinit()
            self._timer_sub = None
        if self.asynchronous and self.refresh_task is not None:
            self.refresh_task.cancel()
            self.refresh_task = None
        self._async_armed = False
        event_loop._current_instance = None

    def disable(self):
        """Pause LVGL task handling (re-entrant; pair with :meth:`enable`)."""
        # Pause LVGL task handling (e.g. while building the UI). Re-entrant.
        self._pause += 1

    def enable(self):
        """Resume LVGL task handling after :meth:`disable`; arms the sync timer."""
        if self._pause > 0:
            self._pause -= 1
        if self._pause == 0:
            self._arm_sync_timer()

    @staticmethod
    def is_running():
        """True when an :class:`event_loop` instance is currently registered."""
        return event_loop._current_instance is not None

    @staticmethod
    def current_instance():
        """Return the active :class:`event_loop`, or ``None``."""
        return event_loop._current_instance

    def task_handler(self, _=None):
        """Run ``lv.task_handler()`` once when not paused and not nested."""
        if self._in_task or self._pause > 0:
            return
        self._in_task = True
        try:
            if lv._nesting.value == 0:
                lv.task_handler()
                if self.refresh_cb:
                    self.refresh_cb()
        except Exception as e:
            if self.exception_sink:
                self.exception_sink(e)
        finally:
            self._in_task = False

    def tick(self):
        """Manually invoke the timer callback once (same path as the shared timer)."""
        self.timer_cb(None)

    def run(self):
        """Blocking forever-tick loop (macOS only; prefer ``runtime.run_forever()``)."""
        if sys.platform == "darwin":
            while True:
                self.tick()

    def _gate_allows(self):
        if ticks_ms is None or self._next_ok_ms is None:
            return True
        # Positive diff means _next_ok_ms is still in the future.
        return ticks_diff(self._next_ok_ms, ticks_ms()) <= 0

    def _arm_gate(self):
        if ticks_ms is None or ticks_add is None:
            return
        # Pace from completion so a slow flush cannot be immediately followed
        # by another (RT-signal backlog under micropython -i).
        self._next_ok_ms = ticks_add(ticks_ms(), self.delay)

    def timer_cb(self, t):
        """Shared-timer callback: advance LVGL time and run/signal task handling.

        Args:
            t: Timer instance (ignored; may be ``None`` from :meth:`tick`).
        """
        # Called from the runtime's shared timer (on the main thread).
        # In async mode the AsyncTimer fires from inside the running asyncio
        # loop, so we can safely arm (create the refresh task) on the first
        # tick -- no need for an external coordinator.
        if self.asynchronous and not self._async_armed:
            self.arm()
        # Advance LVGL time by real elapsed ms. The present-frame gate may
        # skip task_handler when show()/flush is slow (mipidsi ~30ms); if we
        # also skipped tick_inc there, timers ran at ~half wall-clock speed.
        if ticks_ms is not None:
            now = ticks_ms()
            if self._last_tick_ms is None:
                self._last_tick_ms = now
            elapsed = ticks_diff(now, self._last_tick_ms)
            if elapsed > 0:
                lv.tick_inc(elapsed)
                self._last_tick_ms = now
        if not self._gate_allows():
            return
        if self._pause > 0:
            self._arm_gate()
            return
        if self.asynchronous:
            self.refresh_event.set()
            self._arm_gate()
        else:
            self.task_handler()
            self._arm_gate()

    async def async_refresh(self):
        """Asyncio task body: wait for refresh signals and run ``lv.task_handler``."""
        while True:
            await self.refresh_event.wait()
            if lv._nesting.value == 0:
                self.refresh_event.clear()
                try:
                    lv.task_handler()
                except Exception as e:
                    if self.exception_sink:
                        self.exception_sink(e)
                if self.refresh_cb:
                    self.refresh_cb()
                self._arm_gate()

    def default_exception_sink(self, e):
        """Print ``e`` with traceback to stderr (default :attr:`exception_sink`)."""
        sys.print_exception(e)


def main():
    """Initialize LVGL, wire :class:`DisplayDriver`, and enable the event loop.

    Called automatically on ``import display_driver`` when ``board_config``
    provides ``display_drv`` / ``runtime``.
    """
    global _driver_ref, _host_pump_sub
    gc.collect()
    if not lv.is_initialized():
        lv.init()
    # board_config.Runtime arms auto-service immediately (even when
    # needs_refresh is False). Halt every machine.Timer callback before
    # SPIRAM draw_buf_create; re-arm only after buffers exist.
    if runtime is not None:
        runtime.stop_timer()
    loop_inst = event_loop.current_instance()
    if loop_inst is not None:
        # Already-running loop: pause around driver (re)construction.
        loop_inst.disable()
    try:
        if lv.group_get_default() is None:
            lv.group_create().set_default()

        devs = runtime.devices if runtime is not None else []
        _driver_ref = DisplayDriver(
            display_drv,
            devs,
        )
        # Start event_loop only after draw buffers exist (sync path defers
        # on_tick until enable(); still construct after DisplayDriver so
        # host_pump / service cannot arm the shared timer early).
        if loop_inst is None:
            if runtime is not None:
                runtime.claim_display_refresh()
            # PARTIAL: present after every task_handler (blit already wrote the
            # panel FB). Shared DIRECT: present only from flush_is_last.
            _share = bool(getattr(_driver_ref, "_share_fb", False))
            loop_inst = event_loop(
                period_ms=LVGL_PERIOD_MS,
                asynchronous=runtime.timer_async if runtime is not None else False,
                refresh_cb=None if _share else display_drv.show,
            )
        # Keep HOST/SDL draining on the 10 ms Runtime tick while LVGL task_handler
        # runs only every ~30 ms (claim skips Runtime._service_tick).
        # stop_timer() may have wiped callbacks while leaving a stale handle.
        if runtime is not None and (_host_pump_sub is None or runtime._timer is None):
            _host_pump_sub = None
            vds = list(_driver_ref.virtual_devices)

            def _host_pump(_t):
                for vd in vds:
                    vd.poll_host_device()

            _host_pump_sub = runtime.on_tick(_host_pump, period=10, async_=False)
        # Restore Runtime auto-service (touch / QUIT) cleared by stop_timer().
        if runtime is not None:
            runtime._arm_service()
    finally:
        if loop_inst is not None:
            loop_inst.enable()

    if runtime is not None:

        def _lvgl_shutdown_before_quit():
            # Runs from Runtime._handle_quit (device QUIT or at-exit) before the
            # shared timer stops and the display is released. Tear LVGL down in
            # order: stop the event loop, then lv.deinit() to release LVGL's C
            # state so nothing dereferences it during interpreter finalization.
            global _host_pump_sub
            if _host_pump_sub is not None:
                try:
                    _host_pump_sub.deinit()
                except Exception:
                    pass
                _host_pump_sub = None
            inst = event_loop.current_instance()
            if inst is not None:
                inst.deinit()
            try:
                if lv.is_initialized():
                    lv.deinit()
            except Exception:
                pass

        runtime.before_quit = _lvgl_shutdown_before_quit


class _TouchState:
    x = 0
    y = 0
    pressed = False


# CPython: module-level lv.indev_gesture_recognizers_*; MP/CP: indev methods.
_GESTURE_UPDATE = hasattr(lv, "indev_touch_data_t")
# LVGL ``LV_GESTURE_MAX_POINTS`` is 2; finger id is stored as int8_t (-1 = free).
_MAX_GESTURE_TOUCHES = 2
# Windows/pygame often flickers or renumbers finger_id mid-pinch. Track by
# position → stable LVGL slots 0/1, and hold a slot briefly after the OS drops it
# so LVGL does not cancel ONGOING pinch (requires finger_cnt == 2).
_GESTURE_STICKY_MS = 250
_gesture_touches = None
# id(device) -> {slot: (x, y, last_ms)}
_gesture_slots = {}


def _gesture_tick_ms():
    try:
        return int(lv.tick_get())
    except Exception:
        return 0


def _gesture_dist2(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def _gesture_track_slots(dev_key, points, now):
    """Map live contacts to stable slots 0..1 by nearest prior position.

    Returns (pressed dict slot→(x,y), released slot list).
    """
    live = [(int(pt[0]), int(pt[1])) for pt in points]
    prev = _gesture_slots.get(dev_key) or {}
    new_slots = {}
    assigned_live = set()

    # Match against last-known positions (ignore OS finger_id churn).
    if live and prev:
        slot_ids = list(prev.keys())
        if len(live) == 2 and len(slot_ids) == 2:
            s0, s1 = slot_ids[0], slot_ids[1]
            d_same = _gesture_dist2(live[0], prev[s0][:2]) + _gesture_dist2(live[1], prev[s1][:2])
            d_swap = _gesture_dist2(live[0], prev[s1][:2]) + _gesture_dist2(live[1], prev[s0][:2])
            if d_same <= d_swap:
                new_slots[s0] = (live[0][0], live[0][1], now)
                new_slots[s1] = (live[1][0], live[1][1], now)
            else:
                new_slots[s1] = (live[0][0], live[0][1], now)
                new_slots[s0] = (live[1][0], live[1][1], now)
            assigned_live = {0, 1}
        else:
            pairs = []
            for li, xy in enumerate(live):
                for s, (sx, sy, _) in prev.items():
                    pairs.append((_gesture_dist2(xy, (sx, sy)), li, s))
            pairs.sort()
            used_s = set()
            for _, li, s in pairs:
                if li in assigned_live or s in used_s:
                    continue
                assigned_live.add(li)
                used_s.add(s)
                x, y = live[li]
                new_slots[s] = (x, y, now)

    for li, xy in enumerate(live):
        if li in assigned_live:
            continue
        for s in range(_MAX_GESTURE_TOUCHES):
            if s not in new_slots:
                new_slots[s] = (xy[0], xy[1], now)
                assigned_live.add(li)
                break

    # Hold dropped contacts briefly so LVGL keeps finger_cnt == 2.
    for s, (x, y, t) in prev.items():
        if s in new_slots:
            continue
        age = (now - t) & 0xFFFFFFFF
        if age <= _GESTURE_STICKY_MS and len(new_slots) < _MAX_GESTURE_TOUCHES:
            new_slots[s] = (x, y, t)

    released = [s for s in prev if s not in new_slots]
    _gesture_slots[dev_key] = new_slots
    pressed = {s: (xy[0], xy[1]) for s, xy in new_slots.items()}
    return pressed, released


def _gesture_recognizers_update(indev, touches, touch_cnt):
    fn = getattr(lv, "indev_gesture_recognizers_update", None)
    if fn is not None:
        fn(indev, touches, touch_cnt)
    else:
        indev.gesture_recognizers_update(touches, touch_cnt)


def _gesture_recognizers_set_data(indev, data):
    fn = getattr(lv, "indev_gesture_recognizers_set_data", None)
    if fn is not None:
        fn(indev, data)
    else:
        indev.gesture_recognizers_set_data(data)


def _configure_gesture_recognizers(indev):
    """Tune LVGL multitouch recognizers so pinch is not stolen.

    Upstream ``lv_indev_gesture_detect_rotation`` zero-inits its config; with
    ``rotation_angle_rad_threshold == 0``, any tiny twist becomes RECOGNIZED
    and ``recognizers_update`` resets the still-ONGOING pinch. Two-finger
    swipe can steal the same way once the contact center moves
    ``gesture_min_distance`` pixels.
    """
    if not _GESTURE_UPDATE:
        return

    set_rot = getattr(lv, "indev_set_rotation_rad_threshold", None)
    if set_rot is not None:
        set_rot(indev, 3.5)
    elif hasattr(indev, "set_rotation_rad_threshold"):
        indev.set_rotation_rad_threshold(3.5)

    set_md = getattr(lv, "indev_set_gesture_min_distance", None)
    if set_md is not None:
        set_md(indev, 255)
    elif hasattr(indev, "set_gesture_min_distance"):
        indev.set_gesture_min_distance(255)

    # Laptop touchscreens rarely hit the stock 0.75 / 1.5 pinch gates cleanly.
    set_down = getattr(lv, "indev_set_pinch_down_threshold", None)
    set_up = getattr(lv, "indev_set_pinch_up_threshold", None)
    if set_down is not None:
        set_down(indev, 0.92)
    elif hasattr(indev, "set_pinch_down_threshold"):
        indev.set_pinch_down_threshold(0.92)
    if set_up is not None:
        set_up(indev, 1.12)
    elif hasattr(indev, "set_pinch_up_threshold"):
        indev.set_pinch_up_threshold(1.12)


def _gesture_feed(indev, data, device):
    """Feed multipoint contacts into LVGL gesture recognizers when available."""
    global _gesture_touches
    if not _GESTURE_UPDATE:
        return

    points = getattr(device, "points", None)
    if not points:
        points = ((_TouchState.x, _TouchState.y),) if _TouchState.pressed else ()

    dev_key = id(device)
    now = _gesture_tick_ms()
    pressed, released = _gesture_track_slots(dev_key, points or (), now)

    count = len(pressed) + len(released)
    if _gesture_touches is None:
        _gesture_touches = lv.indev_touch_data_t(_MAX_GESTURE_TOUCHES)

    if count == 0:
        _gesture_slots[dev_key] = {}
        _gesture_recognizers_update(indev, _gesture_touches, 0)
        _gesture_recognizers_set_data(indev, data)
        return

    n = count if count <= _MAX_GESTURE_TOUCHES else _MAX_GESTURE_TOUCHES
    ts = now
    idx = 0
    for contact_id, (x, y) in pressed.items():
        if idx >= n:
            break
        t = _gesture_touches[idx]
        t.point = lv.point_t({"x": x, "y": y})
        t.state = lv.INDEV_STATE.PRESSED
        t.id = contact_id
        t.timestamp = ts
        idx += 1
    for contact_id in released:
        if idx >= n:
            break
        t = _gesture_touches[idx]
        t.point = lv.point_t({"x": 0, "y": 0})
        t.state = lv.INDEV_STATE.RELEASED
        t.id = contact_id
        t.timestamp = ts
        idx += 1

    _gesture_recognizers_update(indev, _gesture_touches, idx)
    _gesture_recognizers_set_data(indev, data)
    data.point = lv.point_t({"x": _TouchState.x, "y": _TouchState.y})


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


def create_devices(devs, lv_display, virtual_devices=None):
    """Register eventsys devices as LVGL indevs (pointer / encoder / keypad).

    Args:
        devs: Iterable of eventsys devices from ``runtime.devices``.
        lv_display: LVGL display object to attach indevs to.
        virtual_devices: Optional list mutated when expanding :class:`HostEventsDevice`
            into virtual pointer/keypad devices.

    Returns:
        list: Accumulated virtual devices (for host expansion).
    """
    if virtual_devices is None:
        virtual_devices = []
    for device in devs:
        if device.type in (eventsys.POINTER, eventsys.ENCODER, eventsys.KEYPAD):
            indev = lv.indev_create()
            indev.set_display(lv_display)
            device.user_data = indev
            if device.type == eventsys.POINTER:
                event_cb = _touch_cb
                device.subscribe(event_cb)
                indev.set_type(lv.INDEV_TYPE.POINTER)
                _configure_gesture_recognizers(indev)
            elif device.type == eventsys.ENCODER:
                event_cb = _encoder_cb
                device.subscribe(event_cb)
                indev.set_type(lv.INDEV_TYPE.ENCODER)
            elif device.type == eventsys.KEYPAD:
                event_cb = _keypad_cb
                device.subscribe(event_cb)
                indev.set_type(lv.INDEV_TYPE.KEYPAD)

            # LVGL calls read_cb every period with (indev, data). device.poll
            # only invokes subscribers when there is a new event, so idle
            # reads never wrote data.state/point — taps were invisible.
            def _read_cb(indev_obj, data, _dev=device, _cb=event_cb):
                _dev.poll(indev_obj, data)
                _cb(None, indev_obj, data)
                if _dev.type == eventsys.POINTER:
                    _gesture_feed(indev_obj, data, _dev)

            indev.set_group(lv.group_get_default())
            indev.set_read_cb(_read_cb)
        elif device.type == eventsys.HOST:
            vd = eventsys.VirtualDevices(device)
            virtual_devices.append(vd)
            create_devices(vd.devices, lv_display, virtual_devices)
    return virtual_devices


class DisplayDriver:
    """Bridge a displaysys driver to an LVGL display + input devices.

    Creates the LVGL display, chooses DIRECT (shared framebuffer) or PARTIAL
    render mode, installs flush callbacks, and wires eventsys devices via
    :func:`create_devices`.
    """

    def __init__(
        self,
        display_drv,
        devs=None,
        color_format=lv.COLOR_FORMAT.RGB565,
        blocking=True,
    ):
        """Create LVGL display buffers and register input devices.

        Args:
            display_drv: displaysys driver (BusDisplay, SDLDisplay, FBDisplay, …).
            devs: Iterable of eventsys devices to register as LVGL indevs.
            color_format: LVGL color format (default RGB565).
            blocking: When False, register a bus flush-ready callback for async blit.
        """
        if devs is None:
            devs = []
        gc.collect()
        if display_drv.requires_byteswap:
            self._needs_swap = display_drv.disable_auto_byteswap(True)
        else:
            self._needs_swap = False
        self._color_size = lv.color_format_get_size(color_format)
        self._blocking = blocking
        self._share_fb = False
        self._draw_buf1 = None
        self._draw_buf2 = None
        # Keep Python refs alive for set_buffers panel views (GC must not free).
        self._fb_share = None

        self.lv_display = lv.display_create(display_drv.width, display_drv.height)
        self.lv_display.set_color_format(color_format)

        share = bool(getattr(display_drv, "share_framebuffer", False))
        # Byteswap + shared FB not supported yet — keep PARTIAL blit path.
        fbs = None
        if share and not self._needs_swap:
            try:
                fbs = display_drv.framebuffers()
            except Exception:
                fbs = None

        if fbs is not None:
            buf1, buf2, nbytes, stride = fbs
            packed = int(display_drv.width) * self._color_size
            self._fb_share = (buf1, buf2)
            self._share_fb = True
            self.lv_display.set_flush_cb(self._flush_cb_direct)
            if (
                stride
                and int(stride) != packed
                and hasattr(self.lv_display, "set_buffers_with_stride")
            ):
                self.lv_display.set_buffers_with_stride(
                    buf1, buf2, int(nbytes), int(stride), lv.DISPLAY_RENDER_MODE.DIRECT
                )
            else:
                self.lv_display.set_buffers(buf1, buf2, int(nbytes), lv.DISPLAY_RENDER_MODE.DIRECT)
        else:
            self._draw_buf1 = lv.draw_buf_create(
                display_drv.width, display_drv.height // 10, color_format, 0
            )
            self._draw_buf2 = lv.draw_buf_create(
                display_drv.width, display_drv.height // 10, color_format, 0
            )
            self.lv_display.set_flush_cb(self._flush_cb)
            if not self._blocking:
                display_drv.display_bus.register_callback(self.lv_display.flush_ready)
            self.lv_display.set_draw_buffers(self._draw_buf1, self._draw_buf2)
            self.lv_display.set_render_mode(lv.DISPLAY_RENDER_MODE.PARTIAL)

        self.virtual_devices = create_devices(devs, self.lv_display)

    def _flush_cb_direct(self, disp_drv, area, color_p):
        """DIRECT: LVGL already painted the panel FB; present on last area."""
        if hasattr(display_drv, "_sdl_active") and not display_drv._sdl_active():
            self.lv_display.flush_ready()
            return
        try:
            last = self.lv_display.flush_is_last()
        except Exception:
            last = True
        if last:
            try:
                display_drv.show()
            except Exception:
                pass
        if self._blocking:
            self.lv_display.flush_ready()

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


# Import-time bootstrap (same as before the probe split).
main()
