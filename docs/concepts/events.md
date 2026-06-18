# Events

Input is unified through [`eventsys`](https://github.com/PyDevices/pydisplay/tree/main/src/lib/eventsys) — event names and device types follow PyGame/SDL2 where possible.

## Device types

| Device | Source examples |
|--------|-----------------|
| Touch | Touchscreen, mouse |
| Key / Keypad | Keyboard, matrix keypad |
| Encoder | Rotary encoder, mouse scroll wheel |
| Joystick | Game controller |

The same event types fire regardless of physical hardware — develop on desktop with a mouse, deploy with a touchscreen.

## Brokers

`board_config.py` typically sets up brokers that poll hardware and enqueue events:

- Touch brokers read `touch_read_func`
- Keypad brokers scan GPIO
- Encoder brokers count steps

Use `eventsys` polling in your main loop or integrate with a GUI library's event loop.

## Custom device types

`eventsys.custom_type()` registers application-specific event classes.

## API reference

[Package Reference](../reference/) → `eventsys`.
