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
| `False` | Timer callbacks arrive automatically (MCU `machine.Timer`, librt on Linux, win32 APC on Windows). |
| `True` | Call **`multimer.pump()`** each main-loop iteration (thread/SDL/polling backends). |

`multimer.sleep_ms()` also advances cooperative polling timers while it waits.

### Schedule queue vs pump

On CPython and CircuitPython unix, **`multimer.capabilities()["schedule_queue"]`** is `True`: callbacks posted from worker threads are queued until the main thread calls **`pump()`**. Some backends (for example Linux **`_librt`**) deliver timer signals on the main thread — **`needs_pump()`** is `False` there — but other code may still use **`multimer.schedule`**, so library code that presents frames may still call **`pump()`** when `schedule_queue` is true.

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
multimer.run_forever(poll=runtime.poll, delay_ms=1)
multimer.run_forever(poll=lambda: runtime.quit_requested)

# Async main loop
await multimer.run_forever_async(poll=runtime.poll, delay_ms=10)

# Sync or async entry (MicroPython-safe startup via schedule)
multimer.dual_main(sync_main, async_main, async_mode=False)
```

## Time helpers

MicroPython-compatible names:

- `ticks_ms()`, `ticks_add()`, `ticks_diff()`, `ticks_less()`
- `sleep_ms(ms)` — blocks in sync code; returns an awaitable when called inside a running asyncio loop (`await multimer.sleep_ms(100)`)

## Development / troubleshooting — deadline hooks

!!! warning "Not for application code"
    `set_deadline_hook` / `run_deadline_hook` exist only for **test harnesses and
    interactive debugging**. Leave them unset in production apps. For Playwright
    and WASM main-thread caveats when debugging these hooks, see
    [PyScript troubleshooting](../testing/pyscript-troubleshooting.md).

Some hosts are single-threaded (notably browser WASM / PyScript): a sync
`while True` loop that calls `sleep_ms` holds the main thread, so a background
timer cannot inject “please quit.” For bounded smoke tests, register a
cooperative deadline hook instead:

```python
import multimer

def on_deadline():
    # e.g. set a quit flag your loop already checks
    runtime.request_quit()
    return True

multimer.set_deadline_hook(on_deadline)
try:
    run_demo()
finally:
    multimer.set_deadline_hook(None)  # always clear when done
```

| API | Role |
|-----|------|
| `set_deadline_hook(hook)` | Register a zero-arg callable, or `None` to clear |
| `run_deadline_hook()` | Invoke the hook if set; returns its result or `False` |
| `sleep_ms` | Calls `run_deadline_hook()` before and after sleeping |

`eventsys.Runtime.poll()` also calls `run_deadline_hook()` so loops that poll
without sleeping still hit the deadline. Application demos should keep using
normal quit handling (`runtime.quit_requested`); only harness code should
install a hook.

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
| Linux librt | `_librt` | False | `timer_create` via librt; ctypes on CPython, ffi/uctypes on MicroPython unix. Replaces former **`_ffi`** and **`_ctypes`** modules. |
| Windows APC | `_win32` | False | Waitable timer + `QueueUserAPC`; callbacks run on the main thread during alertable `SleepEx` (see **`sleep_ms`** / **`runtime.poll`**). |
| Thread | `_threading` | True | Background thread + `schedule` queue |
| SDL2 | `_sdl2` | True | `SDL_AddTimer` via **`usdl2`** |
| Polling | `_polling` | True | Cooperative tick list |
| Asyncio | `_async.AsyncTimer` | False | Software timer on the event loop |

Per-implementation fallback when `machine.Timer` is unavailable:

| Implementation | Order tried |
|----------------|-------------|
| CPython win32 | `_win32` → `_threading` → `_sdl2` → `_polling` |
| CPython Linux | `_librt` → `_threading` → `_sdl2` → `_polling` |
| MicroPython unix | `_librt` → `_threading` → `_sdl2` → `_polling` |
| MicroPython win32 | `_polling` (`_threading` / `_sdl2` unavailable or unsafe under WSL) |
| MicroPython unix (no librt) | `_threading` → `_sdl2` → `_polling` |
| CircuitPython desktop | `_threading` → `_sdl2` → `_polling` |

`_polling` is the last resort on every path above.

`tools/test_timers.py` probes each row (plus `multimer.Timer` default) on the host. Run `python tools/run_test_timers.py` for a per-runtime matrix.

### librt backend (`_librt`)

Linux **`timer_create`** / **`timer_settime`** with thread-directed signals (`SIGEV_THREAD_ID`). Callbacks run on the main thread without **`pump()`**.

Binding path inside **`_librt.py`**:

| Host | Binding |
|------|---------|
| CPython linux | ctypes → `libc.so.6` / `librt.so.1` |
| MicroPython unix | ffi + uctypes |

This single module replaced the older split **`multimer._ffi`** (MicroPython) and **`multimer._ctypes`** (CPython) timer backends.

### win32 backend (`_win32`)

Windows **`CreateWaitableTimer`** + **`QueueUserAPC`**. Callbacks run on the main thread during alertable waits — **`multimer.sleep_ms()`** uses **`SleepEx`**, and **`eventsys` `runtime.poll()`** calls **`process_apcs()`** so typical display loops do not need an explicit **`pump()`**.

Tight CPU-only loops (`while True: pass`) still stall timers (unlike Linux librt signals). Use **`sleep_ms(0)`** or **`runtime.poll()`** in the loop if needed.

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
