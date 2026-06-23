# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


from ._schedule import REQUIRES_RUN_QUEUED, schedule


class _TimerBase:
    """
    A class to create a timer with the same API and similar functionality to
    MicroPython's machine.Timer class.
    """

    REQUIRES_RUN_QUEUED = REQUIRES_RUN_QUEUED

    PERIODIC = const(0)
    ONE_SHOT = const(1)

    def __init__(self, id=-1, **kwargs):
        """
        Initializes the timer with the given parameters.

        Args:
            id (int): The timer ID (default is -1).
            **kwargs: Additional keyword arguments.
        """
        self.id = id
        self._busy = False
        self._timer = None
        if kwargs:
            self.init(**kwargs)

    def init(self, *, mode, freq=-1, period=-1, callback=None):
        """
        Initialize the timer.

        Args:
            mode (int): Timer mode (Timer.ONE_SHOT or Timer.PERIODIC).
            freq (int, optional): Timer frequency in Hz. Defaults to -1.
            period (int, optional): Timer period in milliseconds. Ignored if freq is specified. Defaults to -1.
            callback (callable, optional): Callable to execute upon timer expiration. Defaults to None.

        Raises:
            ValueError: If an invalid timer mode or interval is provided.
        """
        if mode in (self.ONE_SHOT, self.PERIODIC):
            self._mode = mode
        else:
            raise ValueError("Invalid timer mode")

        self._interval = int(1000 / freq) if freq > 0 else period
        if self._interval < 1:
            raise ValueError("Invalid freq or period")

        self._callback = callback
        self._start()  # _start() is implemented in subclasses

    def deinit(self):
        """
        Deinitializes the timer.
        """
        while self._busy:
            pass

        self._stop()  # _stop() is implemented in subclasses
        self._mode = None
        self._interval = 0
        self._callback = None
        self._timer = None

    def _handler(self, interval, param=None):
        """
        Internal callback function called when the timer expires.
        SDL2 timers call the handler with the interval and a user-defined parameter,
        while librt timers call the handler with the interval only.
        They are ignored here.

        Args:
            interval (int): The interval at which the timer expires.
            param: User-defined parameter (ignored).

        Returns:
            int: The next interval for SDL2 timers, 0 for one-shot timers.
        """
        if self._busy:
            return

        self._busy = True
        try:
            schedule(self._callback, self)
        except RuntimeError:  # MicroPython: schedule queue may be full
            pass
        self._busy = False

        if self._mode == self.ONE_SHOT:
            self.deinit()
            return 0  # SDL2 expects the callback to return the next interval, 0 for one-shot
        return self._interval

    def _start(self):
        """
        Starts the timer. Must be implemented by subclasses.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def _stop(self):
        """
        Stops the timer. Must be implemented by subclasses.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement this method")
