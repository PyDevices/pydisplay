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
import multimer

async def main():
    while True:
        for event in broker.poll():
            ...  # handle event
        display.show()
        await multimer.sleep_ms(0)  # yield to the event loop

multimer.run(main)
```

## Broker polling

If `broker.poll()` is synchronous, call it inside the async loop and **await a yield each iteration** so touch redraw and timers run. Use `await multimer.sleep_ms(0)` — no need to import asyncio.

For periodic callbacks, use `multimer.AsyncTimer` or `multimer.periodic(..., async_=True)` inside `async def main()` after the loop is running.

## Examples to study

| Script | What to copy |
|--------|--------------|
| `calculator.py` | Full async UI loop |
| `eventsys_simpletest.py` | Minimal poll + await |
| `paint.py` | Touch drawing with asyncio |

Try via: `web/pyscript/load.html?modules=eventsys_simpletest`

## Common failures

| Symptom | Cause |
|---------|-------|
| Frozen tab | Blocking loop, no `await` |
| No touch response | Poll loop never yields |
| Import error | Example needs packages not in `pyscript.toml` manifest |

Regenerate manifest after adding examples: `./scripts/install_refresh_manifests.sh`.

## Next

- [multimer](../concepts/multimer.md)
- [Try pydisplay](../try/index.md)
- [Troubleshooting](../troubleshooting.md)
- [Contributing](../contributing.md) — PyScript PRs welcome

## Reference

- [API reference (core)](../reference/) → `eventsys`, `displaysys.psdisplay`
