multimer provides cross-platform periodic timers compatible with `machine.Timer`.

## Narrative docs

- [multimer concept](../../concepts/multimer.md) — sync/async quick start, public API
- [Runtime](../../concepts/runtime.md) — shared timer via `eventsys.Runtime`
- [Displays — timing](../../concepts/displays.md#timing)
- [PyScript asyncio](../../guides/pyscript-asyncio.md)

## Key entry points

- `multimer.Timer` — platform-selected sync backend (`Timer.PERIODIC` / `Timer.ONE_SHOT`)
- `multimer.AsyncTimer` — asyncio/uasyncio software timer
- `multimer.schedule` — `micropython.schedule`-compatible deferral
- `multimer.asyncio` — lazy-loaded event-loop module
- `multimer.ticks_ms` / `multimer.sleep_ms` / `multimer.monotonic` — portable time primitives
- `multimer.set_deadline_hook` / `multimer.run_deadline_hook` — **dev/troubleshooting only**; cooperative wall-clock deadline for single-threaded harnesses (see [multimer concept — deadline hooks](../../concepts/multimer.md#development--troubleshooting--deadline-hooks))
- `eventsys.Runtime.run_forever` / `run` / `run_async` — application keep-alive and async entry

Timer backends deliver callbacks without an app-level queue-drain step.

Generated API pages for each module appear below (build time).
