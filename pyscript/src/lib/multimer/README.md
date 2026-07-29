# multimer

Cross-platform periodic timers with a `machine.Timer`-style API — sync timers, `AsyncTimer`, millisecond ticks, and sleep helpers on MicroPython, CircuitPython, and CPython.

## Install

### CPython (TestPyPI)

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  multimer
```

### MicroPython (MIP)

```python
import mip
mip.install("multimer", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

## Quick start

```python
import multimer

def on_tick(timer):
    print("tick")

tim = multimer.Timer(-1)
tim.init(mode=multimer.Timer.PERIODIC, period=500, callback=on_tick)

while True:
    multimer.sleep_ms(1000)
```

Async:

```python
import multimer

async def main():
    t = multimer.AsyncTimer(-1)
    t.init(mode=multimer.Timer.PERIODIC, period=200, callback=lambda _: print("async tick"))
    await multimer.asyncio.sleep(2)

multimer.asyncio.run(main())
```

## What you get

- `Timer` — platform backend (librt / win32 / threading / polling; optional SDL2 when `usdl2` is present)
- `AsyncTimer` — asyncio / uasyncio software timer
- `ticks_ms`, `ticks_add`, `ticks_diff`, `ticks_less`, `sleep_ms`, `schedule`
- Lazy `multimer.asyncio` (frozen on MP/CP, stdlib on CPython)

App keep-alive loops live on [eventsys.Runtime](https://test.pypi.org/project/eventsys/) (`run_forever`, `run`, `run_async`).

## Links

- [Documentation — multimer](https://pydisplay.readthedocs.io/en/latest/concepts/multimer/)
- [Source](https://github.com/PyDevices/pydisplay)
- [Issues](https://github.com/PyDevices/pydisplay/issues)
- Related: [eventsys](https://test.pypi.org/project/eventsys/)

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydisplay/blob/main/LICENSE).
