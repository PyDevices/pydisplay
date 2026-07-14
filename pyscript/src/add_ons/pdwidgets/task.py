# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
try:
    from time import ticks_add, ticks_ms
except ImportError:
    from multimer import ticks_add, ticks_ms


class Task:
    """
    A task that runs a callback function after a specified delay.  Used
    by the Display object to run tasks at regular intervals, such as
    refreshing the display or updating the clock.

    Args:
        callback (callable): The function to run.
        delay (int): The delay in milliseconds before running the callback.

    Usage:
        def my_callback():
            print("Hello, world!")

        task = Task(my_callback, 1000)  # Run my_callback every second
        display.add_task(task)
    """

    def __init__(self, callback, delay):
        self.callback = callback
        self.delay = delay
        self.next_run = ticks_add(ticks_ms(), delay)

    def run(self, t):
        """
        Run the callback function and set the next run time.

        Args:
            t (int): The current time in milliseconds.
        """
        self.callback()
        self.next_run = ticks_add(t, self.delay)
