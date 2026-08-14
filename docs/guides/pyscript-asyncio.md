# PyScript asyncio porting

**Who:** You want an existing pydevices-examples example to run in the browser via PyScript.

**Prerequisites:** [PyScript local setup](pyscript.md). Read [Events concept](https://pydevices.github.io/pydevices/eventsys.html) first.

## Why asyncio?

PyScript's runtime is asyncio-based. A typical MCU example:

```python
def main():
    while True:
        for event in runtime.poll():
            handle(event)
        display.show()

main()
```

This blocks the browser event loop. PyScript needs `async def`, `await`, and yields to the scheduler.

## Port pattern

```python
from board_config import display_drv
from app_runtime import runtime
import multimer

async def main():
    while True:
        for event in runtime.poll():
            ...  # handle event
        display_drv.show()
        await multimer.sleep_ms(0)  # yield to the event loop

runtime.run_async(main)
```

Prefer subscribe + keep-alive when you do not need a custom async main:

```python
runtime.on(runtime.events.MOUSEBUTTONDOWN, handle)
runtime.run_forever()
```

## Runtime polling

If `runtime.poll()` is synchronous, call it inside the async loop and **await a yield each iteration** so touch redraw and timers run. Use `await multimer.sleep_ms(0)` — no need to import asyncio.

For periodic callbacks, use `multimer.AsyncTimer` inside `async def main()` after the loop is running.

## Examples to study

| Script | What to copy |
|--------|--------------|
| `calc_graphics.py` | Full async UI loop |
| `eventsys_simpletest.py` | Minimal poll + await |
| `paint.py` | Touch drawing with asyncio |

Try via: `.site/pyscript/micropython.html?modules=eventsys_simpletest`

Minimal shell (no query string): open [`async.html`](https://PyDevices.github.io/pydevices-examples/pyscript/async.html) — a bouncing square that yields with `await multimer.sleep_ms(16)`.

## Common failures

| Symptom | Cause |
|---------|-------|
| Frozen tab | Blocking loop, no `await` |
| No touch response | Poll loop never yields |
| Import error | Example needs packages not in `micropython.toml` manifest |

Regenerate manifest after adding examples: `./scripts/install_refresh_manifests.sh`.

## Next

- [multimer](https://pydevices.github.io/pydevices/multimer.html)
- [Try pydevices-examples](../try/index.md)
- [Troubleshooting](../troubleshooting.md)
- [Contributing](../contributing.md) — PyScript PRs welcome

## Reference

- [pydevices product source](https://github.com/PyDevices/pydevices)
