# PyScript asyncio porting

**Who:** You want an existing pydisplay example to run in the browser via PyScript.

**Prerequisites:** [PyScript local setup](pyscript.md). Read [Events concept](../concepts/events.md) first.

## Why asyncio?

PyScript's runtime is asyncio-based. A typical MCU example:

```python
def main():
    while True:
        for event in broker.poll():
            handle(event)
        display.show()

main()
```

This blocks the browser event loop. PyScript needs `async def`, `await`, and yields to the scheduler.

## Port pattern

```python
import board_config
from board_config import display, broker
from multimer.aio import Timer, run_queued, run

async def main():
    while True:
        for event in broker.poll():
            ...  # handle event
        display.show()
        await run_queued()  # yield to the event loop (optional if you await elsewhere)

run(main)
```

You can use stdlib asyncio instead of the helpers — see [multimer.aio](../concepts/multimer.md#multimeraio-asyncio-timers).

Legacy pattern with raw asyncio:

```python
import asyncio
import board_config
from board_config import display, broker

async def main():
    while True:
        for event in broker.poll():
            ...  # handle event
        display.show()
        await asyncio.sleep(0)  # yield to PyScript

asyncio.get_event_loop().run_until_complete(main())
```

Use `await asyncio.sleep_ms(n)` (MicroPython-style) or `await asyncio.sleep(n/1000)` depending on your PyScript build.

## Broker polling

If `broker.poll()` is synchronous, call it inside the async loop and **await a yield each iteration** so touch redraw and timers run. Use `await run_queued()` from `multimer.aio`, or `await asyncio.sleep(0)` — both are equivalent.

## Examples to study

| Script | What to copy |
|--------|--------------|
| `calculator.py` | Full async UI loop |
| `eventsys_simpletest.py` | Minimal poll + await |
| `paint.py` | Touch drawing with asyncio |

Try via: `html/index.html?script=eventsys_simpletest`

## Common failures

| Symptom | Cause |
|---------|-------|
| Frozen tab | Blocking loop, no `await` |
| No touch response | Poll loop never yields |
| Import error | Example needs packages not in `pyscript.toml` manifest |

Regenerate manifest after adding examples: `./tools/regenerate.sh`.

## Next

- [multimer.aio](../concepts/multimer.md#multimeraio-asyncio-timers)
- [Try pydisplay](../try/index.md)
- [Troubleshooting](../troubleshooting.md)
- [Contributing](../contributing.md) — PyScript PRs welcome

## Reference

- [API reference (core)](../reference/) → `eventsys`, `displaysys.psdisplay`
