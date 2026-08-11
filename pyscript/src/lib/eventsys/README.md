# eventsys

Cross-platform input events with PyGame/SDL2-style types — touch, mouse, keyboard, keypad, encoder, and joystick unified under one `Runtime`.

## Install

### CPython (TestPyPI)

This package is published as a pure-Python wheel to TestPyPI.

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  eventsys
```

Why both indexes: [two-index pip install](https://pydisplay.readthedocs.io/en/latest/publishing-micropython-lib/#two-index-pip-install-required).

Pulls in [multimer](https://test.pypi.org/project/multimer/) for shared timers used by `Runtime`, plus [pydisplay-events](https://test.pypi.org/project/pydisplay-events/) and [pydisplay-keys](https://test.pypi.org/project/pydisplay-keys/).

### MicroPython (MIP)

```python
import mip

mip.install("eventsys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

## Quick start

```python
import events
import eventsys

runtime = eventsys.Runtime()
keypad = eventsys.KeypadDevice(read=lambda: pressed_keys)  # set of key codes
runtime.register(keypad)

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

- `Runtime` — poll / subscribe, display refresh wiring, sync and async keep-alive
- Devices: `TouchDevice`, `KeypadDevice`, `EncoderDevice`, `JoystickDevice`, `HostEventsDevice`
- Optional mappers: `eventsys.touch_keypad`, `eventsys.joystick_keys`
- Event types/key codes: install [`pydisplay-events`](https://test.pypi.org/project/pydisplay-events/) and [`pydisplay-keys`](https://test.pypi.org/project/pydisplay-keys/) (`import events`, `import keys`)

## Links

- [Documentation — eventsys](https://pydisplay.readthedocs.io/en/latest/concepts/events/)
- [Documentation — Runtime](https://pydisplay.readthedocs.io/en/latest/concepts/runtime/)
- [Source](https://github.com/PyDevices/pydisplay)
- [Issues](https://github.com/PyDevices/pydisplay/issues)
- Related: [pydisplay-events](https://test.pypi.org/project/pydisplay-events/), [pydisplay-keys](https://test.pypi.org/project/pydisplay-keys/), [multimer](https://test.pypi.org/project/multimer/), [displaydev](https://test.pypi.org/project/displaydev/)

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydisplay/blob/main/LICENSE).
