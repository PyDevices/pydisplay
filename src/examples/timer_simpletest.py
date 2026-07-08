# multimer types: queued, sync
"""
This is a simple test script that tests the basic functionality of the timer class.

It creates a periodic timer in a class instance and a one-shot timer that stops the periodic timer.
"""

from multimer import Timer, sleep_ms
from sys import platform

try:
    import sys as _sys

    # librt callbacks on MicroPython unix run with the heap locked; defer delivery.
    _timer_hard = _sys.implementation.name != "micropython"
except AttributeError:
    _timer_hard = True

_done = False


class TimerTest:
    def __init__(self):
        self._tim = Timer(-1 if platform == "rp2" else 1)

    def start(self, period):
        self._counter = 0
        self._tim.init(
            mode=Timer.PERIODIC,
            period=period,
            callback=self.do_something,
            hard=_timer_hard,
        )
        print("TimerTest:  timer started...")

    def do_something(self, t):
        self._counter += 1

    def stop(self, t=None):
        global _done
        self._tim.deinit()
        print(f"TimerTest:  timer stopped after {self._counter:,} calls.")
        _done = True


# Create a timer that calls tt.do_something every 1ms
tt = TimerTest()
tt.start(1)

# Create a timer that stops the first timer after 5 seconds
tim2 = Timer(-1 if platform == "rp2" else 2)
tim2.init(mode=Timer.ONE_SHOT, period=5000, callback=tt.stop, hard=_timer_hard)

while not _done:
    sleep_ms(0)
    sleep_ms(1)
