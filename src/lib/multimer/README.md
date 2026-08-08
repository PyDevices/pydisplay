# multimer

Cross-platform periodic timers with a `machine.Timer`-style API — sync timers, `AsyncTimer`, millisecond ticks, and sleep helpers on MicroPython, CircuitPython, and CPython.

## Install

### CPython (TestPyPI)

This package is published as a pure-Python wheel to TestPyPI.

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  multimer
```

Why both indexes: [two-index pip install](https://pydisplay.readthedocs.io/en/latest/publishing-micropython-lib/#two-index-pip-install-required).

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

- `Timer` — auto-selected backend (`machine` → `librt` → `sdl2` → `threading` → `polling`; on CPython `sdl2` skipped when pygame is importable; `AsyncTimer` on PyScript/Jupyter)
- `AsyncTimer` — asyncio / uasyncio software timer
- `ticks_ms`, `ticks_add`, `ticks_diff`, `ticks_less`, `sleep_ms`, `schedule`
- Lazy `multimer.asyncio` (frozen on MP/CP, stdlib on CPython)
- `backend_name`, `backends`, `backends_available`, `use_backend` — inspect or override the backend
- `uses_signals`, `loop_running`, `install_asyncio_compat`

## Choosing a backend

`Timer` picks a backend at import. To inspect or override that choice:

```python
import multimer

multimer.backend_name()  # 'librt', 'machine', 'sdl2', 'threading', …
multimer.backends()  # every name use_backend accepts
multimer.backends_available()  # subset that imports on this host
multimer.use_backend("sdl2")  # rebinds Timer and sleep_ms
```

Setting `MULTIMER_BACKEND` in the environment does the same at import time.
Either way an unavailable backend raises rather than falling back, so a
mis-spelled or unsupported name cannot be mistaken for the platform default.
Call `use_backend` before creating timers.

`polling` is the last auto fallback — required today for **`micropython.exe`
without usdl2** (that port has no `threading`). Desktop GUI vs console
selection matrices live in the
[multimer concept doc](https://pydisplay.readthedocs.io/en/latest/concepts/multimer/#desktop-auto-selection-matrix).

App keep-alive loops live on [eventsys.Runtime](https://test.pypi.org/project/eventsys/) (`run_forever`, `run`, `run_async`).

## Links

- [Documentation — multimer](https://pydisplay.readthedocs.io/en/latest/concepts/multimer/)
- [Source](https://github.com/PyDevices/pydisplay)
- [Issues](https://github.com/PyDevices/pydisplay/issues)
- Related: [eventsys](https://test.pypi.org/project/eventsys/)

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydisplay/blob/main/LICENSE).
