# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Shared machine.Timer-compatible core (internal)."""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


from ._schedule import schedule
from ._ticks import _sleep_ms, ticks_diff, ticks_ms


class _TimerCore:
    """Internal base matching MicroPython machine.Timer semantics."""

    ONE_SHOT = const(0)
    PERIODIC = const(1)

    def __init__(self, id=-1, **kwargs):
        self.id = id
        self._mode = None
        self._period_ms = 0
        self._callback = None
        self._hard = True
        self._busy = False
        self._armed = False
        # Soft path: at most one ``schedule`` entry (or in-flight callback) so a
        # slow tick cannot flood ``micropython.schedule`` under librt signals.
        self._sched_pending = False
        # Wall time of last soft callback completion — used to drop RT-signal
        # backlog so a slow tick cannot busy-loop catch-up frames (MP -i + LVGL).
        self._soft_done_ms = None
        # Minimum idle after the last soft callback before another may schedule.
        # Grown to the callback duration under overload so duty cycle stays
        # ≤ ~50% and an interactive REPL still gets stdin time.
        self._soft_gap_ms = 0
        # Pre-bind for the soft (scheduled) path: evaluating ``self._invoke_callback``
        # allocates a bound method, which fails inside a locked-heap ISR/FFI
        # callback. Bind once here so scheduling touches only stored references.
        self._deliver_cb = self._soft_invoke
        if kwargs:
            self.init(**kwargs)

    def init(self, *, mode=PERIODIC, freq=-1, period=-1, callback=None, hard=True):
        if mode not in (self.ONE_SHOT, self.PERIODIC):
            raise ValueError("Invalid timer mode")

        if self._armed:
            self._disarm()

        period_ms = int(1000 / freq) if freq > 0 else period

        if period_ms < 1:
            raise ValueError("Invalid freq or period")

        self._mode = mode
        self._period_ms = period_ms
        self._callback = callback
        self._hard = hard
        self._sched_pending = False
        self._soft_done_ms = None
        self._soft_gap_ms = period_ms
        self._arm()
        self._armed = True

    def deinit(self):
        self._wait_idle()
        if self._armed:
            self._disarm()
            self._armed = False
        self._mode = None
        self._period_ms = 0
        self._callback = None
        self._hard = True
        self._sched_pending = False
        self._soft_done_ms = None
        self._soft_gap_ms = 0

    def _wait_idle(self):
        while self._busy:
            _sleep_ms(1)

    def _invoke_callback(self, arg):
        cb = self._callback
        # A soft (scheduled) delivery can outlive its timer: deinit() clears the
        # callback while a schedule(_deliver_cb) is still queued (seen on the
        # CircuitPython threading backend during teardown). Skip the stale
        # delivery instead of crashing on the now-None callback.
        if cb is None:
            return
        cb(arg)

    def _soft_invoke(self, arg):
        # Keep ``_sched_pending`` set for the whole callback so overlapping
        # timer signals coalesce instead of enqueueing more schedule entries.
        t0 = ticks_ms()
        try:
            self._invoke_callback(arg)
        finally:
            self._sched_pending = False
            done = ticks_ms()
            self._soft_done_ms = done
            duration = ticks_diff(done, t0)
            gap = self._period_ms
            gap = max(gap, duration)
            # Clamp so a ticks glitch cannot disable soft delivery forever
            # (that left RT signals interrupting sleep with no callback work —
            # rising CPU + dead heartbeats under micropython -i).
            max_gap = self._period_ms * 50 if self._period_ms else 500
            max_gap = max(max_gap, 100)
            max_gap = min(max_gap, 2000)
            gap = min(gap, max_gap)
            self._soft_gap_ms = gap
            # ONE_SHOT cleanup must not run in the librt/FFI signal path
            # (heap locked on MicroPython → MemoryError in timer_settime).
            if self._mode == self.ONE_SHOT:
                self._deinit_oneshot_safe()

    def _deinit_oneshot_safe(self):
        """Disarm a fired ONE_SHOT; absorb heap-locked failures on signal path."""
        try:
            self.deinit()
        except MemoryError:
            # Kernel oneshot already has a zero interval; leak the timer id
            # until process exit rather than allocating under a locked heap.
            pass

    def _deliver(self):
        if self._busy:
            return

        if not self._hard:
            if self._sched_pending:
                # Already queued or running — drop this tick under load.
                return
            # Drop queued RT signals that piled up during a slow callback so we
            # do not immediately schedule another frame (hard lock under -i).
            done = self._soft_done_ms
            gap = self._soft_gap_ms if self._soft_gap_ms else self._period_ms
            if done is not None and gap > 0 and ticks_diff(ticks_ms(), done) < gap:
                return

        self._busy = True
        try:
            if self._hard:
                self._invoke_callback(self)
            else:
                self._sched_pending = True
                try:
                    schedule(self._deliver_cb, self)
                except RuntimeError:
                    # ``schedule queue full`` — drop this tick; next signal retries.
                    self._sched_pending = False
        finally:
            self._busy = False

        if self._mode == self.ONE_SHOT:
            if self._hard:
                # May still be heap-locked on librt+MP FFI; absorb if so.
                self._deinit_oneshot_safe()
            # Soft: ``_soft_invoke`` deinits after the scheduled callback.
            return 0
        return self._period_ms

    def _arm(self):
        raise NotImplementedError

    def _disarm(self):
        raise NotImplementedError
