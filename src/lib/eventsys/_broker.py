# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Event broker: aggregates devices and dispatches subscribers."""

from ._device import Device, device_class, types
from ._events import events


def poll_quit_discarding_others(broker):
    """One poll pass; True if QUIT was seen. Other events in the batch are discarded."""
    if broker is None:
        return False
    if elist := broker.poll():
        for e in elist:
            if e.type == events.QUIT:
                return True
    return False


class _BrokerTimerSubscription:
    """Handle for a callback subscribed to the broker's shared timer.

    Call :meth:`deinit` to stop receiving ticks without affecting other
    subscribers or the underlying timer.
    """

    def __init__(self, broker, entry):
        self._broker = broker
        self._entry = entry

    def deinit(self):
        entry = self._entry
        if entry is None:
            return
        self._entry = None
        try:
            self._broker._tick_callbacks.remove(entry)
        except ValueError:
            pass


class Broker(Device):
    """Polls registered devices and dispatches events to subscribers.

    The broker also owns the single shared periodic timer for a board. Instead
    of each display or GUI subsystem creating its own ``multimer`` timer, they
    subscribe a callback through :meth:`on_tick`; the broker runs one timer and
    fans ticks out to every subscriber. ``multimer`` is imported lazily so
    ``eventsys`` stays importable in isolation and on targets without a timer
    backend.
    """

    type = types.BROKER
    responses = events.filter
    events = events

    def __init__(self):
        super().__init__()
        self.devices = []
        self._device_callbacks = {}
        self._on_quit = None
        self._timer = None
        self._tick_callbacks = []
        self._ticks_ms = None
        self._ticks_add = None
        self._ticks_diff = None

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
        """Subscribe to event types (broker-level). Prefer :meth:`on` / :meth:`on_device`."""
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
        super().subscribe(callback, event_types)

    def unsubscribe(self, callback, event_types=None, device_types=None):
        if device_types is not None:
            if event_types is not None:
                raise ValueError("set one of device_types or event_types but not both.")
            for device_type in device_types:
                self.off(callback, device_type=device_type)
            return
        if event_types is None:
            raise ValueError("event_types is required")
        super().unsubscribe(callback, event_types)

    def create(self, type=types.QUEUE, **kwargs):
        """Create a device, register it, and return it."""
        cls = device_class(type)
        if cls is None:
            raise ValueError("Invalid device type")
        dev = cls(**kwargs)
        self.register(dev)
        return dev

    def register(self, dev):
        """Register a device to be polled."""
        dev.broker = self
        self.devices.append(dev)

    def unregister(self, dev):
        """Remove a device from polling."""
        if dev in self.devices:
            self.devices.remove(dev)
            dev.broker = None

    ############### Shared timer dispatch ################

    def start_timer(self, *, async_=False, tick_ms=10):
        """Create the shared periodic timer that drives :meth:`on_tick` subscribers.

        ``multimer`` is imported lazily here (not at module import) so
        ``eventsys`` remains standalone. ``async_`` selects
        ``multimer.AsyncTimer`` (asyncio hosts such as PyScript/Jupyter) over the
        default ``multimer.Timer``. Returns the underlying timer; a no-op if the
        timer is already running.
        """
        if self._timer is not None:
            return self._timer
        from multimer import AsyncTimer, Timer, ticks_add, ticks_diff, ticks_ms

        self._ticks_ms = ticks_ms
        self._ticks_add = ticks_add
        self._ticks_diff = ticks_diff
        timer_class = AsyncTimer if async_ else Timer
        timer = timer_class(-1)
        timer.init(mode=timer_class.PERIODIC, period=tick_ms, callback=self._dispatch_tick)
        self._timer = timer
        return timer

    def _dispatch_tick(self, timer_obj):
        now = self._ticks_ms()
        for entry in tuple(self._tick_callbacks):
            if self._ticks_diff(entry[2], now) > 0:
                continue
            entry[2] = self._ticks_add(now, entry[1])
            entry[0](timer_obj)

    def on_tick(self, callback, *, period, async_=False):
        """Subscribe ``callback`` to the shared timer, firing about every ``period`` ms.

        Starts the shared timer on first use. Returns a subscription object with
        a ``deinit()`` method that unsubscribes the callback. This is the hook
        display refresh uses instead of the display owning its own timer, and the
        same hook other subsystems (e.g. ``lv_utils``) can use later.
        """
        if not callable(callback):
            raise ValueError("callback is not callable.")
        if self._timer is None:
            self.start_timer(async_=async_)
        entry = [callback, int(period), self._ticks_add(self._ticks_ms(), int(period))]
        self._tick_callbacks.append(entry)
        return _BrokerTimerSubscription(self, entry)

    def stop_timer(self):
        """Stop the shared timer and drop all :meth:`on_tick` subscriptions."""
        self._tick_callbacks = []
        timer = self._timer
        self._timer = None
        if timer is not None:
            timer.deinit()

    def register_quit_cleanup(self, resource, *, before=None, after=None):
        """Wire ``resource.quit()`` to run on ``events.QUIT`` (no process exit)."""
        if not callable(getattr(resource, "quit", None)):
            raise ValueError("resource must have a callable quit() method")

        def _handler():
            try:
                import pydisplay_test_mode

                if pydisplay_test_mode.ENABLED:
                    return
            except ImportError:
                pass
            if before is not None:
                before()
            resource.quit()
            if after is not None:
                after()

        self.on_quit = _handler

    def _handle_quit(self):
        """Invoke the application quit handler without terminating the process."""
        if self._on_quit is not None:
            self._on_quit()

    def quit(self):
        """Run the quit handler (legacy name for :meth:`_handle_quit`)."""
        self._handle_quit()

    @property
    def on_quit(self):
        return self._on_quit

    @on_quit.setter
    def on_quit(self, value):
        if value is not None and not callable(value):
            raise ValueError("on_quit must be callable")
        self._on_quit = value

    def _poll(self):
        eventlist = []
        for device in self.devices:
            dev_events = device.poll()
            if dev_events:
                eventlist.extend(dev_events)
                if callback_list := self._device_callbacks.get(device.type):
                    for func in callback_list:
                        for event in dev_events:
                            func(event)
        return eventlist
