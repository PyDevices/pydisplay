multimer provides cross-platform periodic timers compatible with `machine.Timer`.

## Narrative docs

- [multimer concept](../../concepts/multimer.md) — sync/async quick start, `pump()`, `needs_pump()`
- [Displays — timing](../../concepts/displays.md#timing)
- [PyScript asyncio](../../guides/pyscript-asyncio.md)

## Key entry points

- `multimer.Timer` — platform-selected sync backend
- `multimer.AsyncTimer` — asyncio/uasyncio software timer
- `multimer.periodic()` — convenience factory for periodic callbacks
- `multimer.pump()` — drain schedule queue and cooperative timers
- `multimer.run()` / `multimer.run_forever()` / `multimer.run_forever_async()` — async and sync main-loop helpers
- `multimer.dual_main()` — pick sync or async entry at startup
- `multimer.needs_pump()` / `multimer.capabilities()` — platform introspection
- `multimer.ticks_ms`, `multimer.sleep_ms` — portable time primitives
- `multimer.set_deadline_hook` / `multimer.run_deadline_hook` — **dev/troubleshooting only**; cooperative wall-clock deadline for single-threaded harnesses (see [multimer concept — deadline hooks](../../concepts/multimer.md#development--troubleshooting--deadline-hooks))

Generated API pages for each module appear below (build time).
