# Board devices contract

Normative end-device surface for `board_config` — CircuitPython-like discovery,
stable role names, and a clear split between eager UI devices and lazy extras.

This is the **target** contract. Board configs and drivers live in
[`micropython-hardware`](https://github.com/PyDevices/micropython-hardware);
campaign boards there use the split layout, while many others are still
single-file. Prefer graduating new split boards in that repo rather than
adding `board_devices.py` ad hoc.

Planning notes (agent/internal): [`.cursor/board-device-contract.md`](../../.cursor/board-device-contract.md).

## Specials (always these names)

| Symbol | Required | Notes |
|--------|----------|-------|
| `display_drv` | yes | Display backend |
| `runtime` | when `display_drv.needs_refresh` | [`eventsys.Runtime`](../concepts/runtime.md); may be `None` on display-only MCU boards |

## Optional end-device roles

Omit the name entirely when the hardware is absent. Canonical symbols:

| Role | Symbol | Wiring |
|------|--------|--------|
| Touch | `touch` | Eager in `board_config`; wire into `Runtime`; apps use `runtime.touch_dev` |
| Keypad | `keypad` | All board buttons (not encoder click); apps use `runtime.keypad_dev` |
| Encoder | `encoder` | Includes click; apps use `runtime.encoder_dev` |
| Joystick | `joystick` | Separate from keypad; apps use `runtime.joystick_dev` |
| Addressable LEDs | `pixels` | NeoPixel / DotStar / APA102 |
| Discrete LED | `led` | Primary user LED only |
| Motion | `accelerometer`, `gyroscope`, `magnetometer` | Separate; omit missing axes |
| Environment | `temperature`, `humidity`, `pressure` | Same driver may bind to several names |
| Audio | `audio`, `microphone` | `audio` = playback; `microphone` separate |
| Storage | `sdcard` | Driver object only; no auto-mount |
| Camera | `camera` | |
| Expansion I2C | `i2c` | Dedicated STEMMA/Qwiic/Grove only (not internal-only) |
| Power | `battery` | |
| Field / PHY | `can`, `rs485`, `ethernet` | Dedicated board hardware |
| Wi‑Fi | `wlan` | Station/AP handle; leave high-level `wifi` for add_ons / CP |
| Bluetooth LE | `ble` | Omit when absent |
| Bluetooth Classic | `bt` | BR/EDR; omit when absent |
| RF co-processor | `radio` | AirLift/C6/etc.; may coexist with `wlan`/`ble` |
| Runtime USB device | `usb_device` | Non-tooling `machine.USBDevice`; omit tooling CDC bridge |

Out of contract as `board_config` symbols: high-level `wifi` / `bluetooth` modules
and tooling USB / UART bridges. Apps may still use those stacks directly.

## Discovery

- **Eager UI roles** (`touch`, `keypad`, `encoder`, `joystick`, …): constructed in
  `board_config` and wired into `runtime`. Apps discover them through
  `runtime` (e.g. `runtime.touch_dev is not None`) — not via
  `hasattr(board_config, "touch")` or direct driver access.
- **Lazy roles:** `DEVICES` lists **only** names constructed by `board_devices`.
  Apps check `"name" in board_config.DEVICES` before access so probing does not
  allocate. (`hasattr` on a lazy name may construct — do not use it for discovery.)

`DEVICES` is authored in **`board_devices.DEVICES`** only. `board_config`
re-exports that frozenset; eager UI names are not listed there.

## Module layout (shape to prove)

Keep `board_config.py`. Sibling `board_devices.py` holds `DEVICES`, zero-arg
factories, and `setup_devices`. End of `board_config.py`:

```python
from board_devices import DEVICES, setup_devices
setup_devices(globals())
```

Shared boilerplate is [`boarddev`](../../src/lib/boarddev.py) under `src/lib/`
(name signals *devices*, not `board_config`). Typical
`board_devices.setup_devices` is a thin wrapper around `boarddev.bind_lazy`.
A board may replace `setup_devices` and skip `boarddev` entirely.

There is **no** separate `board_hardware` module.

## Bus ownership

| Bus shared with… | Lives in |
|------------------|----------|
| UI devices (`display_drv`, `touch`, `keypad`, `encoder`, `joystick`, anything wired into `runtime`) | `board_config` |
| Only non-UI lazy devices (e.g. SPI for `sdcard` + `radio`) | `board_devices` (optional) |

Lazy factories import UI-shared buses from `board_config` when needed
(e.g. IMU on the same I2C as touch).

### Infrastructure names (for later sharing)

Rename consistently even before lazy devices exist:

| Kind | Canonical name |
|------|----------------|
| Primary shared I2C | `i2c` |
| Primary shared SPI | `spi` |
| Extra SPI buses | role-qualified: `touch_spi`, `sd_spi`, … |
| Display protocol bus | `display_bus` (SPIBus / I80Bus / FourWire / MIPI `Bus` / …) |
| Primary IO expander | `io_expander` |

## Touch duck-type

`board_config.touch` is the **driver object** used when wiring `Runtime`. Apps
interact via `runtime.touch_dev` / LVGL, not the raw driver.

1. **`touch.read_points()`** → `()` when up, else a sequence of
   `(x, y[, id[, …]])`. Never a bare `(x, y)` from this method (ambiguous with
   a single 2-tuple point). Single-touch chips return `()` or a one-element
   sequence.
2. **Adapters:** `eventsys.TouchDevice` rotates all points, emits primary-finger
   `MOUSE*`, exposes `touch_dev.points`. LVGL `display_driver` feeds gesture
   recognizers when those APIs exist. Non-LVGL apps keep using primary `MOUSE*`.
3. **Board wrappers:** do not collapse multi-touch to `points[0]` in
   `board_config`. Keep only sequence-preserving maps (e.g. diagonal rescale).
4. Wire with `touch_read=touch.read_points` (or a sequence-preserving wrapper).

See [Runtime — touch read contract](../concepts/runtime.md#touch-read-contract)
and [Touch drivers](touch-drivers.md).

## App usage

```python
import board_config as board
from board_config import display_drv, runtime

display_drv.fill(0)

# Eager UI — discover/use through runtime
if runtime is not None and runtime.touch_dev is not None:
    runtime.touch_dev.subscribe(...)

# Lazy extras — DEVICES only (do not hasattr these)
if "sdcard" in board.DEVICES:
    card = board.sdcard  # constructs now
if "wlan" in board.DEVICES:
    wlan = board.wlan
    wlan.active(True)
```

## Rollout

Board configs and drivers live in
[`PyDevices/micropython-hardware`](https://github.com/PyDevices/micropython-hardware).
Ten campaign boards are **graduated** there to the split layout
(`board_config.py` + `board_devices.py`). Remaining boards still use the
single-file `board_config.py` until retrofitted.

| In micropython-hardware now | Still to do |
|-----------------------------|-------------|
| End-device names `touch` / `encoder`; infra buses | Split layout for non-campaign boards |
| Campaign boards: `DEVICES` + lazy factories | Fill remaining lazy factories |
| Sequence-preserving `touch_read` | Mass retrofit of remaining configs |

Sibling inventory / matrix notes:
[micropython-hardware/docs](https://github.com/PyDevices/micropython-hardware/tree/main/docs)
and [device matrix](https://pydevices.github.io/micropython-hardware/).

## See also

- [Board configs](board-configs.md) — how to pick and install a config
- [Runtime](../concepts/runtime.md) — `display_drv` / `runtime` / touch read
- [Architecture](../concepts/architecture.md) — how pieces fit together
