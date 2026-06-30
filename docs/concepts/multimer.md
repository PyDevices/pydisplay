# multimer

Cross-platform periodic timers with a `machine.Timer`-compatible API. One import covers sync timers, async timers, millisecond ticks, sleep, and main-loop helpers.

## Quick start — sync

```python
import multimer

def on_tick(timer):
    print("tick")

tim = multimer.Timer(-1)
tim.init(mode=multimer.PERIODIC, period=500, callback=on_tick)

while True:
    if multimer.needs_pump():
        multimer.pump()
    do_other_work()
    multimer.sleep_ms(1)
```

## Quick start — async

```python
import multimer

async def main():
    tim = multimer.AsyncTimer(-1)
    tim.init(mode=multimer.PERIODIC, period=33, callback=on_tick)
    while True:
        handle_events()
        await multimer.sleep_ms(0)

multimer.run(main)
```

No separate submodule and no `import asyncio` required for these patterns.

## When to call `pump()`

Ask one question: **`multimer.needs_pump()`**

| Answer | What to do |
|--------|------------|
| `False` | Timer callbacks arrive automatically (MCU `machine.Timer`, POSIX backends on Linux). |
| `True` | Call **`multimer.pump()`** each main-loop iteration (thread/SDL/polling backends). |

`multimer.sleep_ms()` also advances cooperative polling timers while it waits.

### Schedule queue vs pump

On CPython and CircuitPython unix, **`multimer.capabilities()["schedule_queue"]`** is `True`: callbacks posted from worker threads are queued until the main thread calls **`pump()`**. Some backends (for example Linux **`_posix`**) deliver timer signals on the main thread — **`needs_pump()`** is `False` there — but other code may still use **`multimer.schedule`**, so library code that presents frames may still call **`pump()`** when `schedule_queue` is true.

Inspect the platform:

```python
import multimer

print(multimer.capabilities())
print(multimer.backend_name())
```

## Convenience API

```python
# One-liner periodic timer (auto-allocates timer id)
t = multimer.periodic(callback, period=33)
t = multimer.periodic(callback, period=33, async_=True)

# Context manager
with multimer.Timer(-1) as t:
    t.init(mode=multimer.PERIODIC, period=100, callback=cb)
    ...

# Blocking main loop (``poll()`` may return ``True`` to exit cleanly)
multimer.run_forever(poll=broker.poll, delay_ms=1)
multimer.run_forever(poll=lambda: eventsys.poll_quit_discarding_others(broker))

# Async main loop
await multimer.run_forever_async(poll=broker.poll, delay_ms=10)

# Sync or async entry (MicroPython-safe startup via schedule)
multimer.dual_main(sync_main, async_main, async_mode=False)
```

## Time helpers

MicroPython-compatible names:

- `ticks_ms()`, `ticks_add()`, `ticks_diff()`, `ticks_less()`
- `sleep_ms(ms)` — blocks in sync code; returns an awaitable when called inside a running asyncio loop (`await multimer.sleep_ms(100)`)

## Async helpers

| Function | Purpose |
|----------|---------|
| `AsyncTimer` | Software timer backed by asyncio/uasyncio |
| `run(main)` | Run a coroutine — `asyncio.run` on desktop, background task in Jupyter/PyScript |
| `run_forever_async(poll=…)` | Async version of `run_forever` |
| `dual_main(…)` | Choose sync or async startup |

`AsyncTimer.init()` must run while the event loop is already running (typically inside `async def main()`).

## FAQ — callback did not fire

1. **`needs_pump()` is True** — call `pump()` (or `sleep_ms`, which pumps cooperative timers).
2. **Async timer** — event loop must be running at `init()`; await something each loop (`await sleep_ms(0)`).
3. **Timer deinited** — one-shot and `deinit()` stop callbacks.
4. **Exception in callback** — on CPython callbacks re-raise by default; set `multimer.ON_CALLBACK_ERROR = "log"` to log instead.

## pydisplay integration

pydisplay uses multimer for `auto_refresh`, LVGL ticks, and frame pacing. Display drivers pass **`async_=True`** to `periodic()` on PyScript/Jupyter hosts. See [Displays — timing](displays.md#timing).

## Internals (contributors)

Backend selection at import (first match wins):

| Backend | Module | `needs_pump` | Notes |
|---------|--------|--------------|-------|
| MCU hardware | `machine.Timer` | False | On-device only |
| Linux POSIX | `_posix` | False | librt timers; ctypes on CPython, ffi/uctypes on MicroPython unix. Replaces former **`_ffi`** and **`_ctypes`** modules. |
| Thread | `_threading` | True | Background thread + `schedule` queue |
| SDL2 | `_sdl2` | True | `SDL_AddTimer` via **`usdl2`** |
| Polling | `_polling` | True | Cooperative tick list |
| Asyncio | `_async.AsyncTimer` | False | Software timer on the event loop |

`examples/test_timers.py` probes each row (plus `multimer.Timer` default) when the module imports on the host. Run `python tools/run_test_timers.py` for a per-runtime matrix.

### POSIX backend (`_posix`)

Linux **`timer_create`** / **`timer_settime`** with thread-directed signals (`SIGEV_THREAD_ID`). Callbacks run on the main thread without **`pump()`**.

Binding path inside **`_posix.py`**:

| Host | Binding |
|------|---------|
| CPython linux | ctypes → `libc.so.6` / `librt.so.1` |
| MicroPython unix | ffi + uctypes |

This single module replaced the older split **`multimer._ffi`** (MicroPython) and **`multimer._ctypes`** (CPython) timer backends.

### SDL2 bindings (`usdl2`)

Desktop SDL2 access is shared between display and timer code:

| Consumer | Import chain |
|----------|--------------|
| `displaysys.sdldisplay` | built-in `usdl2` → `add_ons/usdl2.py` |
| `multimer._sdl2` | `usdl2` (native or `add_ons/usdl2.py`) |

Both prefer the native **`usdl2`** module when it is frozen or built into the interpreter. Pure-Python fallbacks keep CPython and MicroPython Unix working without it. See [Displays — SDLDisplay](displays.md#sdldisplay) and [MicroPython — usdl2](../platforms/micropython.md#usdl2-native-sdl2).

## Next

- [Displays — timing](displays.md#timing)
- [Events](events.md)
- [PyScript asyncio](../guides/pyscript-asyncio.md)
