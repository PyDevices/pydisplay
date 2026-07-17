# eventsys

Cross-platform input events with PyGame/SDL2-style types — touch, mouse, keyboard, keypad, encoder, and joystick unified under one `Runtime`.

## Install

### CPython (TestPyPI)

```bash
pip install \
  -i https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  eventsys
```

Pulls in [multimer](https://test.pypi.org/project/multimer/) for shared timers used by `Runtime`.

### MicroPython (MIP)

```python
import mip
mip.install("eventsys", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

## Quick start

```python
import eventsys

runtime = eventsys.Runtime()
keypad = eventsys.KeypadDevice(read=lambda: pressed_keys)  # set of key codes
runtime.register(keypad)

while True:
    for event in runtime.poll():
        if event.type == eventsys.KEYDOWN:
            print("down", event.key)
        elif event.type == eventsys.QUIT:
            break
```

Subscribe instead of polling:

```python
runtime.on(eventsys.KEYDOWN, lambda e: print(e))
runtime.run_forever()
```

## What you get

- `Runtime` — poll / subscribe, display refresh wiring, sync and async keep-alive
- Devices: `TouchDevice`, `KeypadDevice`, `EncoderDevice`, `JoystickDevice`, `HostEventsDevice`
- Event constants and namedtuples (`KEYDOWN`, `MOUSEBUTTONDOWN`, …) plus `Keys` / quit chords
- Optional mappers: `eventsys.touch_keypad`, `eventsys.joystick_keys`

## Links

- [Documentation — eventsys](https://pydisplay.readthedocs.io/en/latest/concepts/events/)
- [Documentation — Runtime](https://pydisplay.readthedocs.io/en/latest/concepts/runtime/)
- [Source](https://github.com/PyDevices/pydisplay)
- [Issues](https://github.com/PyDevices/pydisplay/issues)
- Related: [multimer](https://test.pypi.org/project/multimer/), [displaysys](https://test.pypi.org/project/displaysys/)

## License

MIT — see [LICENSE](https://github.com/PyDevices/pydisplay/blob/main/LICENSE).
