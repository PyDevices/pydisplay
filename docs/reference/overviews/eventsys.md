eventsys unifies input from touchscreens, mice, keypads, keyboards, encoders, and joysticks into PyGame/SDL2-style events.

## Narrative docs

- [Events concept](../../concepts/events.md) — poll loop, subscribe, and built-in devices
- [Architecture](../../concepts/architecture.md) — brokers and board_config
- [Touch drivers](../../hardware/touch-drivers.md) — chip-level helpers

## Key entry points

- `Broker` — aggregates devices; `poll()` always returns a list
- `poll_quit_discarding_others(broker)` — one poll pass; `True` if `QUIT` seen (display-only loops)
- `TouchDevice`, `KeypadDevice`, `EncoderDevice`, `QueueDevice`, `JoystickDevice`
- `events` — event type constants and namedtuple event classes
- `Keys` — SDL key code table
- `register_event`, `register_device` — application extensions
- `capabilities()` — dialect and device introspection

Generated API pages for each module appear below (build time).
