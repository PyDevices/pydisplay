# multimer

Cross-platform periodic timers with a `machine.Timer`-compatible API. One import covers sync timers, async timers, millisecond ticks, sleep, and optional main-loop helpers.

## Public surface

```python
from multimer import (
    Timer,              # sync; platform backend selected at import
    AsyncTimer,         # asyncio/uasyncio software timer
    schedule,           # micropython.schedule-compatible
    sleep_ms,           # Adafruit-style sleep (awaitable inside a running loop)
    ticks_ms,
    ticks_add,
    ticks_diff,
    ticks_less,
    monotonic,
    asyncio,            # lazy: frozen on MP/CP, stdlib on CPython
    set_deadline_hook,  # test/debug only
    run_deadline_hook,  # test/debug only
)
```

Mode constants live on the timer class (`Timer.PERIODIC`, `Timer.ONE_SHOT`), not on the module.

Lazy helpers (also importable as `multimer.run`, etc.): `run`, `run_forever`, `run_forever_async`, `dual_main`.

There is **no** public `pump()`, `needs_pump()`, `periodic()`, `capabilities()`, or `backend_name()`.

## Quick start — sync

```python
import multimer

def on_tick(timer):
    print("tick")

tim = multimer.Timer(-1)
tim.init(mode=multimer.Timer.PERIODIC, period=500, callback=on_tick)

while True:
    # Keep the main thread alertable / cooperative (esp. Win32 APC backends).
    multimer.sleep_ms(1)
```

On hosted pydisplay apps, prefer `runtime.poll()` (or `multimer.run_forever(poll=…)`) instead of a bare busy loop — see [Runtime](runtime.md).

## Quick start — async

```python
import multimer

async def main():
    tim = multimer.AsyncTimer(-1)
    tim.init(mode=multimer.AsyncTimer.PERIODIC, period=33, callback=on_tick)
    while True:
        handle_events()
        await multimer.sleep_ms(0)

multimer.run(main)
```

No separate submodule and no `import asyncio` required for these patterns. `AsyncTimer.init()` must run while the event loop is already running (typically inside `async def main()`).

## Convenience / loop helpers

```python
# Context manager
with multimer.Timer(-1) as t:
    t.init(mode=multimer.Timer.PERIODIC, period=100, callback=cb)
    ...

# Blocking main loop (``poll()`` may return a truthy value to exit)
multimer.run_forever(poll=runtime.poll, delay_ms=1)
multimer.run_forever(poll=lambda: runtime.quit_requested)

# Async main loop
await multimer.run_forever_async(poll=runtime.poll, delay_ms=10)

# Sync or async entry
multimer.dual_main(sync_main, async_main, async_mode=False)
```

`run(coro)` blocks until completion on desktop/MCU; on Jupyter/PyScript (loop already running) it schedules a background task and returns.

## Time helpers

MicroPython-compatible names:

- `ticks_ms()`, `ticks_add()`, `ticks_diff()`, `ticks_less()`
- `monotonic()` — monotonic clock (seconds-scale float/int depending on host)
- `sleep_ms(ms)` — blocks in sync code; returns an awaitable when called inside a running asyncio loop (`await multimer.sleep_ms(100)`)

`sleep_ms` is a plain sleep helper. It is **not** an application-facing “drain timers” API.

## `schedule`

`multimer.schedule(callback, arg)` matches `micropython.schedule` semantics where available. On CPython/CircuitPython, callbacks scheduled from a non-main thread are queued and run on the main thread when `schedule` / loop helpers next run pending work. Prefer keeping timer callbacks on the main thread (the default backends aim for that).

## Development / troubleshooting — deadline hooks

!!! warning "Not for application code"
    `set_deadline_hook` / `run_deadline_hook` exist only for **test harnesses and
    interactive debugging**. Leave them unset in production apps, and expect to
    use them only from test/debug tooling that already understands your host's
    threading model (notably single-threaded browser WASM).

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
| `run_forever` / `run_forever_async` | Poll until `poll()` is truthy |
| `dual_main(…)` | Choose sync or async startup |
| `asyncio` | Lazy-loaded event-loop module |

## FAQ — callback did not fire

1. **Main loop never yields** — call `sleep_ms` or `runtime.poll()` so alertable/cooperative backends can deliver (especially Win32 APC).
2. **Async timer** — event loop must be running at `init()`; await something each loop (`await sleep_ms(0)`).
3. **Timer deinited** — one-shot and `deinit()` stop callbacks.
4. **Exception in callback** — exceptions propagate from the delivery path; fix the callback or catch inside it.

## pydisplay integration

pydisplay owns the shared periodic timer through `eventsys.Runtime` (`on_tick`, auto-refresh when `display_drv.needs_refresh`). Apps normally poll via `runtime.poll()` / `run_forever` rather than allocating their own display-refresh timer. Use `Timer` when `runtime.timer_async` is false and `AsyncTimer` when it is true (PyScript/Jupyter; desktop override via `PYDISPLAY_TIMER_ASYNC`). See [Runtime](runtime.md) and [Displays — timing](displays.md#timing).

## Internals (contributors)

Backend selection for sync `Timer` (simplified; first usable match wins):

| Backend | Hosts | Notes |
|---------|-------|-------|
| MCU `machine.Timer` | On-device MicroPython / CircuitPython | Hardware timer |
| `_librt` | Linux CPython / MicroPython unix | `timer_create`; callbacks on main thread via signals |
| `_win32` | Windows | Waitable timer + APC; alertable waits via `sleep_ms` / `runtime.poll` |
| `_threading` | Fallback | Background thread |
| `_sdl2` | Fallback | `SDL_AddTimer` via `usdl2` when available |
| Polling / async-only | WASM, Jupyter | Prefer `AsyncTimer` |

`tools/test_timers.py` probes public timers on the host. Run `python tools/run_test_timers.py` for a per-runtime matrix. Private backend probing is opt-in (`MULTIMER_PROBE_BACKENDS=1`).

### librt backend (`_librt`)

Linux **`timer_create`** / **`timer_settime`** with thread-directed signals (`SIGEV_THREAD_ID`). Callbacks run on the main thread.

### win32 backend (`_win32`)

Windows **`CreateWaitableTimer`** + **`QueueUserAPC`**. Callbacks run on the main thread during alertable waits — **`multimer.sleep_ms()`** and **`eventsys.Runtime.poll()`** keep the thread alertable. Tight CPU-only loops (`while True: pass`) still stall timers; use **`sleep_ms(0)`** or **`runtime.poll()`**.

### SDL2 bindings (`usdl2`)

Desktop SDL2 access is shared between display and timer code:

| Consumer | Import chain |
|----------|--------------|
| `displaysys.sdldisplay` | built-in `usdl2` → `add_ons/usdl2.py` |
| `multimer` SDL backend | `usdl2` (native or `add_ons/usdl2.py`) |

Both prefer the native **`usdl2`** module when it is frozen or built into the interpreter. See [Displays — SDLDisplay](displays.md#sdldisplay) and [MicroPython — usdl2](../platforms/micropython.md#usdl2-native-sdl2).

## Next

- [Runtime](runtime.md)
- [Displays — timing](displays.md#timing)
- [Events](events.md)
- [PyScript asyncio](../guides/pyscript-asyncio.md)
