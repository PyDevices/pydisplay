multimer provides cross-platform periodic timers compatible with `machine.Timer`.

## Narrative docs

- [multimer concept](../../concepts/multimer.md) — default `Timer`, **`multimer.aio`**, when to use `run_scheduled` / `run`
- [Displays — timing](../../concepts/displays.md#timing)
- [PyScript asyncio](../../guides/pyscript-asyncio.md)

## Key entry points

- `multimer.Timer` — platform-selected backend (MCU, POSIX, SDL, threads)
- `multimer.run_scheduled` — sync queue drain (threading/SDL backends)
- `multimer.aio` — opt-in asyncio `Timer`, optional `run_scheduled` / `run` helpers

Generated API pages for each module appear below (build time).
