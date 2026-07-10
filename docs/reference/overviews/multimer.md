multimer provides cross-platform periodic timers compatible with `machine.Timer`.

## Narrative docs

- [multimer concept](../../concepts/multimer.md) — sync/async quick start, public API, loop helpers
- [Runtime](../../concepts/runtime.md) — shared timer via `eventsys.Runtime`
- [Displays — timing](../../concepts/displays.md#timing)
- [PyScript asyncio](../../guides/pyscript-asyncio.md)

## Key entry points

- `multimer.Timer` — platform-selected sync backend (`Timer.PERIODIC` / `Timer.ONE_SHOT`)
- `multimer.AsyncTimer` — asyncio/uasyncio software timer
- `multimer.schedule` — `micropython.schedule`-compatible deferral
- `multimer.run()` / `multimer.run_forever()` / `multimer.run_forever_async()` — async and sync main-loop helpers
- `multimer.dual_main()` — pick sync or async entry at startup
- `multimer.ticks_ms` / `multimer.sleep_ms` / `multimer.monotonic` — portable time primitives
- `multimer.set_deadline_hook` / `multimer.run_deadline_hook` — **dev/troubleshooting only**; cooperative wall-clock deadline for single-threaded harnesses (see [multimer concept — deadline hooks](../../concepts/multimer.md#development--troubleshooting--deadline-hooks))

There is no public `pump()`, `needs_pump()`, or `periodic()`.

Generated API pages for each module appear below (build time).
