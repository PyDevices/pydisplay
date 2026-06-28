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
- `multimer.needs_pump()` / `multimer.capabilities()` — platform introspection
- `multimer.run()` / `multimer.run_forever_async()` — async helpers
- `multimer.ticks_ms`, `multimer.sleep_ms` — portable time primitives

Generated API pages for each module appear below (build time).
