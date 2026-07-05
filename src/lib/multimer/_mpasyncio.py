# SPDX-FileCopyrightText: 2024 Brad Barnett
# SPDX-FileCopyrightText: 2019 Damien P. George
#
# SPDX-License-Identifier: MIT
#
# Minimal asyncio event loop for MicroPython builds that ship ``_asyncio`` but
# not frozen ``asyncio`` / ``uasyncio`` (e.g. micropython.exe standard).
# Adapted from MicroPython extmod/asyncio/core.py.

from _asyncio import Task, TaskQueue
import sys

from ._ticks import ticks_add, ticks_diff
from ._ticks import ticks_ms as ticks

try:
    import select
except ImportError:
    select = None


class CancelledError(BaseException):
    pass


class TimeoutError(Exception):
    pass


_exc_context = {"message": "Task exception wasn't retrieved", "exception": None, "future": None}


class SingletonGenerator:
    def __init__(self):
        self.state = None
        self.exc = StopIteration()

    def __iter__(self):
        return self

    def __next__(self):
        if self.state is not None:
            _task_queue.push(cur_task, self.state)
            self.state = None
            return None
        self.exc.__traceback__ = None
        raise self.exc


_sleep_ms_sgen = SingletonGenerator()


class Event:
    def __init__(self):
        self.state = False
        self.waiting = TaskQueue()

    def is_set(self):
        return self.state

    def set(self):
        while self.waiting.peek():
            _task_queue.push(self.waiting.pop())
        self.state = True

    def clear(self):
        self.state = False

    def wait(self):
        if not self.state:
            self.waiting.push(cur_task)
            cur_task.data = self.waiting
            yield
        return True


def sleep_ms(t, sgen=_sleep_ms_sgen):
    assert sgen.state is None
    sgen.state = ticks_add(ticks(), max(0, t))
    return sgen


def sleep(t):
    return sleep_ms(int(t * 1000))


class IOQueue:
    def __init__(self):
        if select is None:
            raise ImportError("_mpasyncio IOQueue requires select")
        self.poller = select.poll()
        self.map = {}

    def _enqueue(self, s, idx):
        if id(s) not in self.map:
            entry = [None, None, s]
            entry[idx] = cur_task
            self.map[id(s)] = entry
            self.poller.register(s, select.POLLIN if idx == 0 else select.POLLOUT)
        else:
            sm = self.map[id(s)]
            assert sm[idx] is None
            assert sm[1 - idx] is not None
            sm[idx] = cur_task
            self.poller.modify(s, select.POLLIN | select.POLLOUT)
        cur_task.data = self

    def _dequeue(self, s):
        del self.map[id(s)]
        self.poller.unregister(s)

    def queue_read(self, s):
        self._enqueue(s, 0)

    def queue_write(self, s):
        self._enqueue(s, 1)

    def remove(self, task):
        while True:
            del_s = None
            for k in self.map:
                q0, q1, s = self.map[k]
                if q0 is task or q1 is task:
                    del_s = s
                    break
            if del_s is not None:
                self._dequeue(s)
            else:
                break

    def wait_io_event(self, dt):
        for s, ev in self.poller.ipoll(dt):
            sm = self.map[id(s)]
            if ev & ~select.POLLOUT and sm[0] is not None:
                _task_queue.push(sm[0])
                sm[0] = None
            if ev & ~select.POLLIN and sm[1] is not None:
                _task_queue.push(sm[1])
                sm[1] = None
            if sm[0] is None and sm[1] is None:
                self._dequeue(s)
            elif sm[0] is None:
                self.poller.modify(s, select.POLLOUT)
            else:
                self.poller.modify(s, select.POLLIN)


def _promote_to_task(aw):
    return aw if isinstance(aw, Task) else create_task(aw)


def create_task(coro):
    if not hasattr(coro, "send"):
        raise TypeError("coroutine expected")
    t = Task(coro, globals())
    _task_queue.push(t)
    return t


def ensure_future(aw):
    return _promote_to_task(aw)


def run_until_complete(main_task=None):
    global cur_task
    excs_all = (CancelledError, Exception)
    excs_stop = (CancelledError, StopIteration)
    while True:
        dt = 1
        while dt > 0:
            dt = -1
            t = _task_queue.peek()
            if t:
                dt = max(0, ticks_diff(t.ph_key, ticks()))
            elif not _io_queue.map:
                cur_task = None
                if not main_task or not main_task.state:
                    return
                dt = 3
            _io_queue.wait_io_event(dt)

        t = _task_queue.pop()
        cur_task = t
        try:
            exc = t.data
            if not exc:
                t.coro.send(None)
            else:
                t.data = None
                t.coro.throw(exc)
        except excs_all as er:
            assert t.data is None
            awaited = t is main_task
            if awaited:
                cur_task = None
                if not isinstance(er, StopIteration):
                    t.state = False
                    raise er
                if t.state is None:
                    t.state = False
            if t.state:
                if t.state is True:
                    t.state = False if awaited else None
                elif callable(t.state):
                    t.state(t, er)
                    t.state = False
                    awaited = True
                else:
                    while t.state.peek():
                        _task_queue.push(t.state.pop())
                        awaited = True
                    t.state = False
                if not awaited and not isinstance(er, excs_stop):
                    _task_queue.push(t)
                t.data = er
            elif t.state is None:
                t.data = exc
                _exc_context["exception"] = exc
                _exc_context["future"] = t
                Loop.call_exception_handler(_exc_context)
            if t is main_task:
                return er.value


def run(coro):
    return run_until_complete(create_task(coro))


async def _stopper():
    pass


cur_task = None
_stop_task = None


class Loop:
    _exc_handler = None

    def create_task(coro):
        return create_task(coro)

    def run_forever():
        global _stop_task
        _stop_task = Task(_stopper(), globals())
        run_until_complete(_stop_task)

    def run_until_complete(aw):
        return run_until_complete(_promote_to_task(aw))

    def stop():
        global _stop_task
        if _stop_task is not None:
            _task_queue.push(_stop_task)
            _stop_task = None

    def close():
        pass

    def set_exception_handler(handler):
        Loop._exc_handler = handler

    def get_exception_handler():
        return Loop._exc_handler

    def default_exception_handler(loop, context):
        print(context["message"], file=sys.stderr)
        print("future:", context["future"], "coro=", context["future"].coro, file=sys.stderr)
        sys.print_exception(context["exception"], sys.stderr)

    def call_exception_handler(context):
        (Loop._exc_handler or Loop.default_exception_handler)(Loop, context)


def get_event_loop(runq_len=0, waitq_len=0):
    return Loop


def get_running_loop():
    if cur_task is None:
        raise RuntimeError("no running event loop")
    return Loop


def current_task():
    if cur_task is None:
        raise RuntimeError("no running event loop")
    return cur_task


def new_event_loop():
    global _task_queue, _io_queue
    _task_queue = TaskQueue()
    _io_queue = IOQueue()
    return Loop


new_event_loop()
