eventsys unifies input from touchscreens, mice, keypads, keyboards, encoders, and joysticks into PyGame/SDL2-style events.

## Narrative docs

- [Events concept](../../concepts/events.md) — poll loop and subscribe
- [Architecture](../../concepts/architecture.md) — brokers and board_config
- [Touch drivers](../../hardware/touch-drivers.md) — chip-level helpers

## Key entry points

- `Broker` — queues events from devices; call `poll()` in your main loop
- `Device` subclasses — `TouchDevice`, `KeypadDevice`, `EncoderDevice`, …
- `events` — event type constants and namedtuple event classes

Generated API pages for each module appear below (build time).
