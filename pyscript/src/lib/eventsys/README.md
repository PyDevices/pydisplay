# eventsys

Optional cross-platform event traffic controller for applications using PyGame/SDL2-style events. It unifies touch, mouse, keyboard, keypad, encoder, and joystick input under one app-owned `Runtime`.

`eventsys` is not part of a board definition and is not required by LVGL. Board configs expose hardware and read callables; a non-LVGL app can choose `eventsys`, provide another coordinator, or handle those devices directly.

## Install

### CPython (TestPyPI)

This package is published as a pure-Python wheel to TestPyPI.

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pydevices-eventsys
```

Why both indexes: [two-index pip install](https://pydisplay.readthedocs.io/en/latest/publishing-micropython-lib/#two-index-pip-install-required).

Pulls in `pydevices-multimer` for shared timers used by `Runtime`, plus `pydevices-events` and `pydevices-keys`. Python imports remain `multimer`, `events`, and `keys`.

### MicroPython (MIP)

```python
import mip

mip.install("eventsys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

## Quick start

```python
import events
import eventsys
import board_config

runtime = eventsys.Runtime.from_board_config(board_config)

while True:
    for event in runtime.poll():
        if event.type == events.KEYDOWN:
            print("down", event.key)
        elif event.type == events.QUIT:
            break
```

Subscribe instead of polling:

```python
runtime.on(events.KEYDOWN, lambda e: print(e))
runtime.run_forever()
```

## What you get

- `Runtime` — an optional app-level traffic controller with poll / subscribe, display refresh wiring, and sync/async keep-alive
- Devices: `TouchDevice`, `KeypadDevice`, `EncoderDevice`, `JoystickDevice`, `HostEventsDevice`
- Optional mappers: `eventsys.touch_keypad`, `eventsys.joystick_keys`
- Event types/key codes: install `pydevices-events` and `pydevices-keys` (`import events`, `import keys`)

## Links

- [Documentation — eventsys](https://pydisplay.readthedocs.io/en/latest/concepts/events/)
- [Documentation — Runtime](https://pydisplay.readthedocs.io/en/latest/concepts/runtime/)
- [Source](https://github.com/PyDevices/micropython-hardware)
- [Issues](https://github.com/PyDevices/micropython-hardware/issues)
- Related TestPyPI distributions: `pydevices-events`, `pydevices-keys`, `pydevices-multimer`, `pydevices-displaydev`

## License

MIT — see [LICENSE](https://github.com/PyDevices/micropython-hardware/blob/main/LICENSE).
