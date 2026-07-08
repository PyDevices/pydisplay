# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Board runtime: aggregates devices, shared timer, and quit lifecycle."""

from ._encoder import EncoderDevice
from ._events import events
from ._host import HostEventsDevice
from ._joystick import JoystickDevice
from ._keypad import KeypadDevice
from ._touch import TouchDevice

DEFAULT_REFRESH_MS = 33


def _validate_callable(value, name):
    if not callable(value):
        raise TypeError(f"{name} must be callable")


def _validate_rotation_table(table):
    if table is None:
        return
    try:
        length = len(table)
    except TypeError as exc:
        raise TypeError("touch_rotation_table must be a 4-item sequence") from exc
    if length != 4:
        raise ValueError("touch_rotation_table must have exactly 4 items")


class _RuntimeTimerSubscription:
    """Handle for a callback subscribed to the runtime's shared timer."""

    def __init__(self, runtime, entry):
        self._runtime = runtime
        self._entry = entry

    def deinit(self):
        entry = self._entry
        if entry is None:
            return
        self._entry = None
        try:
            self._runtime._tick_callbacks.remove(entry)
        except ValueError:
            pass


class _DisplayRefreshClaim:
    def __init__(self, runtime):
        self._runtime = runtime

    def release(self):
        self._runtime._resume_display_refresh()


class _DisplayRefreshPaused:
    def __init__(self, runtime):
        self._runtime = runtime
        self._claim = None

    def __enter__(self):
        self._claim = self._runtime.claim_display_refresh()
        return self._claim

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._claim is not None:
            self._claim.release()
        return False


class Runtime:
    """Board runtime: input devices, shared timer, display refresh, and quit lifecycle.

    ``multimer`` is imported lazily when the shared timer starts so ``eventsys``
    remains importable in isolation.
    """

    events = events

    def __init__(
        self,
        display=None,
        host_read=None,
        touch_read=None,
        touch_rotation_table=None,
        *,
        refresh_period=None,
        timer_async=False,
    ):
        self.devices = []
        self._event_callbacks = {}
        self._device_callbacks = {}
        self._display = display
        self._before_quit = None
        self._quit_requested = False
        self._timer_async = bool(timer_async)
        self._timer = None
        self._tick_callbacks = []
        self._ticks_ms = None
        self._ticks_add = None
        self._ticks_diff = None
        self._refresh_subscription = None
        self._refresh_paused = False
        self._refresh_claim = None
        self.host_dev = None
        self.touch_dev = None
        self.keypad_dev = None
        self.encoder_dev = None
        self.joystick_dev = None

        if host_read is not None:
            _validate_callable(host_read, "host_read")
            if display is None:
                raise ValueError("host_read requires display=")
            self.host_dev = HostEventsDevice(host_read=host_read, display=display)
            self.register(self.host_dev)

        if touch_read is not None:
            _validate_callable(touch_read, "touch_read")
            if display is None:
                raise ValueError("touch_read requires display=")
            _validate_rotation_table(touch_rotation_table)
            self.touch_dev = TouchDevice(
                read=touch_read,
                display=display,
                rotation_table=touch_rotation_table,
            )
            self.register(self.touch_dev)

        if display is not None:
            self._wire_display_refresh(refresh_period)
            self._install_default_quit()

    @property
    def timer_async(self):
        return self._timer_async

    @property
    def quit_requested(self):
        return self._quit_requested

    @property
    def before_quit(self):
        return self._before_quit

    @before_quit.setter
    def before_quit(self, value):
        if value is not None and not callable(value):
            raise ValueError("before_quit must be callable")
        self._before_quit = value

    @property
    def display_refresh(self):
        return self._refresh_subscription

    def on(self, event_type, callback):
        """Subscribe ``callback`` to one or more event types."""
        if not callable(callback):
            raise ValueError("callback is not callable.")
        if isinstance(event_type, (list, tuple)):
            for et in event_type:
                self.on(et, callback)
            return
        self.subscribe(callback, event_types=[event_type])

    def on_device(self, device_type, callback):
        """Subscribe ``callback`` to all events from devices of ``device_type``."""
        if not callable(callback):
            raise ValueError("callback is not callable.")
        callback_set = self._device_callbacks.get(device_type, set())
        callback_set.add(callback)
        self._device_callbacks[device_type] = callback_set

    def off(self, callback, event_type=None, device_type=None):
        """Unsubscribe ``callback`` from an event type or device type."""
        if device_type is not None:
            if callback_set := self._device_callbacks.get(device_type):
                callback_set.discard(callback)
        elif event_type is not None:
            self.unsubscribe(callback, event_types=[event_type])
        else:
            raise ValueError("set event_type or device_type")

    def subscribe(self, callback, event_types=None, device_types=None):
        """Subscribe to event types (runtime-level). Prefer :meth:`on` / :meth:`on_device`."""
        if not callable(callback):
            raise ValueError("callback is not callable.")
        if device_types is not None:
            if event_types is not None:
                raise ValueError("set one of device_types or event_types but not both.")
            for device_type in device_types:
                self.on_device(device_type, callback)
            return
        if event_types is None:
            raise ValueError("event_types is required")
        for event_type in event_types:
            callback_set = self._event_callbacks.get(event_type, set())
            callback_set.add(callback)
            self._event_callbacks[event_type] = callback_set

    def unsubscribe(self, callback, event_types=None, device_types=None):
        if device_types is not None:
            if event_types is not None:
                raise ValueError("set one of device_types or event_types but not both.")
            for device_type in device_types:
                self.off(callback, device_type=device_type)
            return
        if event_types is None:
            raise ValueError("event_types is required")
        for event_type in event_types:
            if callback_set := self._event_callbacks.get(event_type):
                callback_set.discard(callback)

    def register(self, dev):
        """Register a device to be polled."""
        dev.runtime = self
        self.devices.append(dev)

    def unregister(self, dev):
        """Remove a device from polling."""
        if dev in self.devices:
            self.devices.remove(dev)
            dev.runtime = None

    def add_keypad(self, read):
        _validate_callable(read, "read")
        self.keypad_dev = KeypadDevice(read=read)
        self.register(self.keypad_dev)
        return self.keypad_dev

    def add_encoder(self, read, *, button_read=None, button=2):
        _validate_callable(read, "read")
        if button_read is not None:
            _validate_callable(button_read, "button_read")
        self.encoder_dev = EncoderDevice(read=read, read2=button_read, data=button)
        self.register(self.encoder_dev)
        return self.encoder_dev

    def add_joystick(self, *, joystick_driver=None, **kwargs):
        self.joystick_dev = JoystickDevice(joystick_driver=joystick_driver, **kwargs)
        self.register(self.joystick_dev)
        return self.joystick_dev

    def poll(self):
        """Poll all registered devices and return aggregated events."""
        eventlist = []
        for device in self.devices:
            dev_events = device.poll()
            if dev_events:
                eventlist.extend(dev_events)
                if callback_list := self._device_callbacks.get(device.type):
                    for func in callback_list:
                        for event in dev_events:
                            func(event)
                for event in dev_events:
                    if callback_list := self._event_callbacks.get(event.type):
                        for func in callback_list:
                            func(event)
        return eventlist

    def start_timer(self, *, async_=False, tick_ms=10):
        """Create the shared periodic timer. Returns the underlying timer."""
        if self._timer is not None:
            return self._timer
        from multimer import AsyncTimer, Timer, ticks_add, ticks_diff, ticks_ms

        self._ticks_ms = ticks_ms
        self._ticks_add = ticks_add
        self._ticks_diff = ticks_diff
        timer_class = AsyncTimer if async_ else Timer
        timer = timer_class(-1)
        timer.init(
            mode=timer_class.PERIODIC,
            period=tick_ms,
            callback=self._dispatch_tick,
            hard=False,
        )
        self._timer = timer
        return timer

    def _dispatch_tick(self, timer_obj):
        now = self._ticks_ms()
        for entry in tuple(self._tick_callbacks):
            if entry[3]:
                continue
            if self._ticks_diff(entry[2], now) > 0:
                continue
            entry[2] = self._ticks_add(now, entry[1])
            entry[0](timer_obj)

    def on_tick(self, callback, *, period, async_=False):
        """Subscribe ``callback`` to the shared timer (about every ``period`` ms)."""
        if not callable(callback):
            raise ValueError("callback is not callable.")
        if self._timer is None:
            self.start_timer(async_=async_)
        entry = [callback, int(period), self._ticks_add(self._ticks_ms(), int(period)), False]
        self._tick_callbacks.append(entry)
        return _RuntimeTimerSubscription(self, entry)

    def stop_timer(self):
        """Stop the shared timer and drop all :meth:`on_tick` subscriptions."""
        self._tick_callbacks = []
        timer = self._timer
        self._timer = None
        self._refresh_subscription = None
        self._refresh_paused = False
        self._refresh_claim = None
        if timer is not None:
            timer.deinit()

    def claim_display_refresh(self):
        """Pause runtime-driven ``display.show()`` while a GUI layer presents frames."""
        if self._refresh_claim is not None:
            raise RuntimeError("display refresh already claimed")
        if self._refresh_subscription is None:
            return _DisplayRefreshClaim(self)
        self._refresh_paused = True
        self._refresh_claim = _DisplayRefreshClaim(self)
        return self._refresh_claim

    def _resume_display_refresh(self):
        if self._refresh_claim is None:
            return
        self._refresh_paused = False
        self._refresh_claim = None

    def display_refresh_paused(self):
        """Context manager that claims and releases display refresh."""
        return _DisplayRefreshPaused(self)

    def _wire_display_refresh(self, refresh_period):
        display = self._display
        if display is None:
            return
        if refresh_period is None:
            wire = bool(getattr(display, "needs_refresh", False))
            period = DEFAULT_REFRESH_MS
        else:
            refresh_period = int(refresh_period)
            wire = refresh_period > 0
            period = refresh_period if wire else DEFAULT_REFRESH_MS
        if not wire:
            return

        def _show(timer_obj):
            if self._refresh_paused:
                return
            display.show(timer_obj)

        self._refresh_subscription = self.on_tick(_show, period=period, async_=self._timer_async)

    def _install_default_quit(self):
        display = self._display
        if display is None or not callable(getattr(display, "quit", None)):
            return
        # Quit side effects run from _handle_quit when devices emit QUIT.
        self._default_quit_display = display

    def _handle_quit(self):
        if self._quit_requested:
            return
        self._quit_requested = True
        try:
            import pydisplay_test_mode

            if pydisplay_test_mode.ENABLED:
                return
        except ImportError:
            pass
        if self._before_quit is not None:
            self._before_quit()
        display = self._display
        if display is not None and callable(getattr(display, "quit", None)):
            display.quit()
        self.stop_timer()
