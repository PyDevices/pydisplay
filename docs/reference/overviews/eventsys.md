eventsys unifies input from touchscreens, mice, keypads, keyboards, encoders, and joysticks into PyGame/SDL2-style events.

## Narrative docs

- [Events concept](../../concepts/events.md) — poll loop, subscribe, and built-in devices
- [Runtime concept](../../concepts/runtime.md) — board_config contract and auto-refresh
- [Architecture](../../concepts/architecture.md) — runtime and board_config

## Key entry points

- `Runtime` — aggregates devices; `poll()` always returns a list
- `quit_requested` — sticky flag set after quit is processed (display-only loops)
- `TouchDevice`, `KeypadDevice`, `EncoderDevice`, `HostEventsDevice`, `JoystickDevice`
- Device type constants: `HOST`, `POINTER` (was `TOUCH`; matches LVGL `INDEV_TYPE.POINTER`), `ENCODER`, `KEYPAD`, `JOYSTICK`
- Optional mappers (import explicitly — not loaded by `import eventsys`): `eventsys.touch_keypad.TouchKeypad`, `eventsys.joystick_keys.JoystickKeys`
- `events` — event type constants and namedtuple event classes
- `Keys` — SDL key code table
- `register_event`, `register_device` — application extensions
- `capabilities()` — dialect and device introspection

Generated API pages for each module appear below (build time).
