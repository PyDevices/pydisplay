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
SERVICE_TICK_MS = 10


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


def _main_file():
    """Return ``__main__.__file__``, or ``None`` at a bare REPL.

    MicroPython often leaves ``sys.modules['__main__']`` as ``None`` while a
    file runs; ``import __main__`` still yields the real module.  ``None`` means
    bare REPL; ``'<stdin>'`` means stdin-as-script (not a live REPL).
    """
    import sys

    m = sys.modules.get("__main__")
    if m is None:
        try:
            import __main__ as m
        except Exception:
            return None
    return getattr(m, "__file__", None)


def _cmdline_has_dash_i(cmdline_path="/proc/self/cmdline"):
    """True if process cmdline contains a ``-i`` token (Linux unix ports).

    MicroPython strips ``-i`` from ``sys.argv`` but leaves it on
    ``/proc/self/cmdline``. Missing procfs (MCU, Windows) returns False.
    """
    try:
        with open(cmdline_path, "rb") as f:
            toks = [t for t in f.read().split(b"\0") if t]
    except Exception:
        return False
    return b"-i" in toks


def _is_interactive_session():
    """True when a REPL prompt will remain after current top-level work.

    CPython: ``sys.flags.interactive`` (``python -i …``) or bare REPL
    (``__main__.__file__ is None``; bare ``python`` often has interactive=0).

    MicroPython and similar: ``-i`` on ``/proc/self/cmdline``, or bare REPL
    via ``__main__.__file__ is None``. No env vars; no reserved filenames.
    """
    import sys

    if getattr(sys.implementation, "name", "") == "cpython":
        flags = getattr(sys, "flags", None)
        return bool(getattr(flags, "interactive", 0)) or (_main_file() is None)
    return _cmdline_has_dash_i() or (_main_file() is None)


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
        self._pending_async_refresh = None
        self._pending_sync_refresh = None
        # Auto-service: the shared timer tick pumps/drains events and polls
        # devices so the canonical idiom needs no user loop. Disabled the moment
        # the app calls poll() itself (legacy loops) to avoid double-pumping.
        self._service_subscription = None
        self._pending_service = None
        self._pending_timer_async = False
        self._app_drives_poll = False
        self._in_service_poll = False
        self._pending_teardown = False
        self._teardown_done = False
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
            self._register_atexit()

        print(f"Runtime: timer_async={self._timer_async}.")

    @property
    def timer_async(self):
        return self._timer_async

    @staticmethod
    def _event_loop_running():
        """True when asyncio already has a running loop (PyScript, Jupyter, async main)."""
        import sys

        if sys.platform in ("emscripten", "webassembly"):
            return True
        try:
            from multimer import asyncio

            if hasattr(asyncio, "get_running_loop"):
                asyncio.get_running_loop()
                return True
        except (ImportError, RuntimeError):
            pass
        return False

    def arm_async_refresh(self):
        """Wire deferred display refresh + auto-service once the loop is running."""
        pending = self._pending_async_refresh
        if pending is not None:
            self._pending_async_refresh = None
            show_fn, period = pending
            self._refresh_subscription = self.on_tick(show_fn, period=period, async_=True)
        if self._pending_service:
            self._pending_service = False
            self._service_subscription = self.on_tick(
                self._service_tick, period=SERVICE_TICK_MS, async_=True
            )
        # Safety net: if on_tick subscriptions were recorded before the loop was
        # running (deferred async timer) but nothing above started the timer,
        # start it now that a loop exists so those callbacks dispatch.
        if self._pending_timer_async and self._timer is None:
            self.start_timer(async_=True)

    async def run(self, tick_ms=SERVICE_TICK_MS):
        """Run the app until quit — asyncio-native entry for ``timer_async`` apps.

        Arms the deferred async refresh + auto-service (an ``AsyncTimer`` needs a
        running loop), then yields until a QUIT is handled. Use it as the async
        idiom::

            import asyncio  # or: from multimer import asyncio
            # ... build UI, define callbacks ...
            asyncio.run(runtime.run())      # or: await runtime.run()

        Sync mode does not need this: the shared timer keeps servicing the app
        after the script falls through to the interpreter.
        """
        from multimer import asyncio

        self.arm_async_refresh()
        while not self._quit_requested:
            await asyncio.sleep(tick_ms / 1000)
        # Teardown here runs outside the service tick (this coroutine is a
        # separate task from the AsyncTimer), so stopping the timer is safe.
        self._perform_teardown()

    def run_forever(self, tick_ms=SERVICE_TICK_MS):
        """Universal blocking entry — identical client code for every backend.

        Apps always end with ``runtime.run_forever()``; the branch taken is
        internal, so the same source runs sync or async, interactive or not:

        * async, a loop already running (PyScript/Jupyter): arm the auto-service
          on that loop and return — the host loop keeps the app alive.
        * async, no running loop (desktop ``timer_async``): ``asyncio.run(self.run())``.
        * sync, signal-delivered backend, interactive session (``-i`` or bare
          REPL then ``import``): return immediately — the REPL stays alive and
          the RT signal drives the auto-service, so a keep-alive loop is
          optional here.
        * sync otherwise: block until quit, then tear down.

        The coroutine :meth:`run` stays public for ``await`` composition inside an
        existing async app or PyScript top-level await.
        """
        import multimer

        if self._timer_async:
            if self._event_loop_running():
                self.arm_async_refresh()
                return
            from multimer import asyncio

            asyncio.run(self.run())
            return

        # Interactive + signal-delivered: timer keeps the app live at the REPL;
        # blocking here would wedge the session needlessly.
        if _is_interactive_session() and multimer.signal_delivered():
            return
        try:
            while not self._quit_requested:
                multimer.sleep_ms(tick_ms)
        finally:
            self._perform_teardown()

    def run_async(self, coro_or_fn):
        """Run a bespoke async entry point, respecting an already-running loop.

        Counterpart to :meth:`run_forever` for apps with their own async
        ``main()`` (rather than the ``on_tick``/``poll`` idiom). Arms the
        deferred async refresh, then:

        * no loop running yet (desktop ``timer_async``): blocks until the
          coroutine finishes via ``asyncio.run``.
        * a loop already running (Jupyter, PyScript): schedules the coroutine
          as a background task and returns immediately.

        ``coro_or_fn`` may be a zero-arg async function or a coroutine object.
        """
        from multimer import asyncio

        async def _runner():
            self.arm_async_refresh()
            coro = coro_or_fn() if callable(coro_or_fn) else coro_or_fn
            return await coro

        if self._event_loop_running():
            return asyncio.create_task(_runner())
        return asyncio.run(_runner())

    @property
    def quit_requested(self):
        return self._quit_requested

    def request_quit(self):
        """Request a clean shutdown (same path as a device QUIT event).

        Useful from application code and from development deadline hooks
        registered via ``multimer.set_deadline_hook``.
        """
        self._handle_quit()

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

    @staticmethod
    def _sync_refresh_needs_deferred_arm():
        """True when sync timers need a poll/sleep drain loop (SDL2, Win32 APC)."""
        try:
            from multimer._select import _drain

            return _drain is not None
        except ImportError:
            return False

    def _maybe_arm_pending_sync_refresh(self):
        pending = self._pending_sync_refresh
        if pending is None:
            return
        show_fn, period = pending
        self._pending_sync_refresh = None
        self._refresh_subscription = self.on_tick(
            show_fn,
            period=period,
            async_=False,
        )

    @staticmethod
    def _drain_timers():
        try:
            from multimer._schedule import _run_pending
            from multimer._select import _drain

            _run_pending()
            if _drain is not None:
                _drain()
        except ImportError:
            pass

    def _service_tick(self, timer_obj):
        """Shared-timer callback: pump/drain events and poll devices.

        Lets the canonical idiom (build UI, define callbacks, fall through to
        the interpreter) stay live with no user loop. Skips while a GUI layer
        (e.g. LVGL) has claimed display refresh — that layer drives input via
        its own device reads — and once the app polls itself (legacy loops).
        """
        if self._quit_requested or self._app_drives_poll or self._refresh_claim is not None:
            return
        self._in_service_poll = True
        try:
            self.poll()
        finally:
            self._in_service_poll = False

    def poll(self):
        """Poll all registered devices and return aggregated events.

        Also invokes ``multimer.run_deadline_hook()`` when present so test
        harnesses can enforce a wall-clock deadline on single-threaded hosts.
        Application code should not rely on that hook.

        An external call (not from the runtime's own auto-service tick) hands
        polling to the application: the auto-service stops pumping so events are
        not drained twice.
        """
        if not self._in_service_poll:
            self._app_drives_poll = True
        try:
            from multimer import run_deadline_hook

            run_deadline_hook()
        except ImportError:
            pass
        self._drain_timers()
        self._maybe_arm_pending_sync_refresh()
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

    def _ensure_ticks(self):
        """Bind the ``multimer`` ticks helpers (needed even before the timer)."""
        if self._ticks_ms is not None:
            return
        from multimer import ticks_add, ticks_diff, ticks_ms

        self._ticks_ms = ticks_ms
        self._ticks_add = ticks_add
        self._ticks_diff = ticks_diff

    def start_timer(self, *, async_=False, tick_ms=10):
        """Create the shared periodic timer. Returns the underlying timer."""
        if self._timer is not None:
            return self._timer
        from multimer import AsyncTimer, Timer

        self._ensure_ticks()
        self._pending_timer_async = False
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
        """Subscribe ``callback`` to the shared timer (about every ``period`` ms).

        Safe to call before the event loop is running in ``timer_async`` apps
        (the canonical idiom builds UI at import time): an ``AsyncTimer`` needs a
        running loop, so timer creation is deferred to :meth:`arm_async_refresh`
        while the callback is recorded now — it dispatches as soon as the timer
        starts.
        """
        if not callable(callback):
            raise ValueError("callback is not callable.")
        self._ensure_ticks()
        if self._timer is None:
            if async_ and not self._event_loop_running():
                self._pending_timer_async = True
            else:
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
        self._pending_async_refresh = None
        self._pending_sync_refresh = None
        self._service_subscription = None
        self._pending_service = None
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
        # Auto-service the shared timer (poll/pump/drain + device dispatch) even
        # when the display needs no periodic refresh, so input and QUIT work in
        # the canonical no-loop idiom. Always armed — including under test mode,
        # since the harness now relies on it too; apps that poll() themselves
        # make it back off (``_app_drives_poll``) and GUI layers via
        # ``_refresh_claim``.
        self._arm_service()
        try:
            import pydisplay_test_mode

            # Test mode still skips the periodic refresh show-timer so examples
            # that call show() themselves avoid a competing refresh.
            if pydisplay_test_mode.ENABLED:
                return
        except ImportError:
            pass
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

        if self._timer_async and not self._event_loop_running():
            self._pending_async_refresh = (_show, period)
            return

        if self._sync_refresh_needs_deferred_arm():
            self._pending_sync_refresh = (_show, period)
            return

        self._refresh_subscription = self.on_tick(
            _show,
            period=period,
            async_=self._timer_async,
        )

    def _arm_service(self):
        """Subscribe the auto-service tick to the shared timer.

        Sync: arm now (starts the shared timer, so the canonical idiom self-
        drives even when the display refresh is deferred). Async: defer until a
        loop is running (``AsyncTimer`` requires it), armed by
        :meth:`arm_async_refresh` / :meth:`run`.
        """
        if self._service_subscription is not None or self._pending_service:
            return
        if self._timer_async and not self._event_loop_running():
            self._pending_service = True
            return
        self._service_subscription = self.on_tick(
            self._service_tick, period=SERVICE_TICK_MS, async_=self._timer_async
        )

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
        # When QUIT is detected from inside the auto-service tick, defer the hard
        # teardown: stopping/deiniting the shared timer from within its own
        # callback is unsafe (the async timer would cancel its running task,
        # wedging the loop). Sync keep-alive / ``run()`` exit finally tear down;
        # async hosts without a keep-alive (PyScript) must schedule teardown.
        if self._in_service_poll:
            self._pending_teardown = True
            self._schedule_deferred_teardown()
            return
        self._perform_teardown()

    def _schedule_deferred_teardown(self):
        """Run :meth:`_perform_teardown` after the current timer callback returns."""
        if self._teardown_done:
            return
        if self._timer_async:
            try:
                from multimer import asyncio

                async def _later():
                    await asyncio.sleep(0)
                    self._perform_teardown()

                asyncio.create_task(_later())
                return
            except Exception:
                pass
            try:
                from js import window
                from pyscript.ffi import create_proxy

                window.setTimeout(create_proxy(lambda *_args: self._perform_teardown()), 0)
                return
            except Exception:
                pass
        # Sync: ``run_forever`` / ``run`` finally or atexit will tear down.

    def _perform_teardown(self):
        """Stop the shared timer and release the display (idempotent)."""
        if self._teardown_done:
            return
        self._teardown_done = True
        self._quit_requested = True
        self._pending_teardown = False
        try:
            import pydisplay_test_mode

            if pydisplay_test_mode.ENABLED:
                # Still run before_quit (autotest / LVGL hooks); skip display.quit only.
                if self._before_quit is not None:
                    self._before_quit()
                self.stop_timer()
                return
        except ImportError:
            pass
        if self._before_quit is not None:
            self._before_quit()
        # Stop the shared timer *before* releasing the display so no in-flight
        # tick callback (refresh / device poll / GUI task handler) touches freed
        # display resources during teardown.
        self.stop_timer()
        display = self._display
        if display is not None and callable(getattr(display, "quit", None)):
            display.quit()

    def _register_atexit(self):
        """Run a clean shutdown when the interpreter exits.

        The canonical idiom keeps the app alive via a persistent interpreter
        (an interactive ``-i`` session, the REPL, or a microcontroller) rather
        than an explicit run loop; the shared timer keeps firing in the
        background. When that interpreter finally exits, stop the timers and
        quit the display so nothing is left running. Registered here (not in a
        GUI add-on) so plain graphical apps get the same clean teardown.

        CPython exposes ``atexit``; MicroPython / CircuitPython expose
        ``sys.atexit`` (single callback). Both run at normal interpreter exit;
        a hard ``os._exit`` (e.g. the test harness) intentionally bypasses it.
        """
        try:
            import atexit

            atexit.register(self._perform_teardown)
            return
        except ImportError:
            pass
        import sys

        if hasattr(sys, "atexit"):
            sys.atexit(self._perform_teardown)
