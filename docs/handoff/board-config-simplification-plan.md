# Plan: simplified board_config with broker-constructor wiring

Status: **proposal / discussion doc** — no code changes yet.

## Goal

Keep the recent architectural decision that **the shared periodic timer is owned
by `eventsys.Broker`** (`Broker.on_tick` / `Broker.stop_timer`), *not* by
display drivers, while making `board_config.py` files shorter, harder to get
wrong, and friendlier to code generation. The batch-generated MCU configs
(busdisplay, fbdisplay, epaperdisplay, pixeldisplay) predate the broker-timer
refactor and follow the older wiring idioms; rather than hand-porting each one
to the current idiom, this plan proposes a single constructor-based idiom and
regenerates everything once.

The proposed canonical flow for every `board_config.py`:

1. Create the bus (if this platform needs one — SPI/I80/I2C, framebuffer, …)
2. Create `display_drv`
3. Create the input device (touch chip, buttons, joystick, …)
4. Create a small wrapper function if the driver doesn't already return what
   the broker expects (e.g. `(x, y)` or `None` for touch)
5. Define the touch rotation table
6. Create the broker, passing `display_drv`, the touch-read function, and the
   rotation table as parameters:

```python
broker = eventsys.Broker(
    display_drv=display_drv,
    touch_read=touch_read_func,
    touch_rotation_table=touch_rotation_table,
)
```

The `Broker` constructor then performs, internally and consistently, what
today has to be hand-written in each config: create the touch device, wire
periodic display refresh onto the shared timer (only for displays that need
it), and register quit cleanup that releases the display and stops the timer.

---

## The three layouts

### 1. Original layout (repo state on Jan 1, 2026 — commit `ef14624e`)

- `eventsys` was a single `eventsys/devices.py` module; configs used
  `from eventsys import devices`, `devices.Broker()`, and
  `broker.create_device(type=devices.types.TOUCH, ...)`.
- **The display owned the refresh timer.** `DisplayDriver.__init__` accepted
  `auto_refresh` and, when truthy, created its own timer:

  ```python
  # displaysys/__init__.py (Jan 2026)
  if auto_refresh:
      period = 33 if isinstance(auto_refresh, bool) else auto_refresh
      from multimer import get_timer
      self._timer = get_timer(self.show, period=period)
  ```

  Desktop drivers (`SDLDisplay`, `PGDisplay`) hard-coded
  `super().__init__(auto_refresh=True)`, so desktop configs never mentioned
  refresh at all — the timer was invisible, buried in the display.
- Quit handling: `broker.quit_func` defaulted to the builtin `exit` (killed
  the process; unfriendly to the REPL and to test harnesses).

### 2. Current layout (`main` today)

- `eventsys.Broker()` owns the one shared timer. Subsystems subscribe with
  `broker.on_tick(callback, period=...)`; the display only provides `show()`.
- `board_config.py` is responsible for the wiring, by hand:

  ```python
  broker = eventsys.Broker()

  touch_dev = broker.create(
      type=eventsys.TOUCH,
      read=touch_read_func,
      data=display_drv,          # opaque name: the display
      data2=touch_rotation_table,  # opaque name: the rotation table
  )

  # Desktop / framebuffer-present backends only:
  broker.display_refresh = broker.on_tick(display_drv.show, period=33)
  broker.register_quit_cleanup(display_drv, after=broker.stop_timer)
  ```

- The refresh subscription handle is stored on `broker.display_refresh` so a
  GUI layer (LVGL via `add_ons/display_driver.py`, or an app like
  `tower_climb`) can take over presenting frames.
- Problem: this is 3–5 lines of policy that every one of the ~135
  `board_config.py` files must reproduce exactly. Today the four
  desktop/hosted configs (`sdldisplay`, `pgdisplay`, `jndisplay`,
  `psdisplay`) and `src/lib/board_config.py` do it correctly; the ~53
  MCU configs that create input devices still use the old
  `data=`/`data2=` idiom, and none of them wires
  `after=broker.stop_timer` (harmless today only because no MCU config
  starts the timer).

### 3. Proposed layout

`board_config.py` becomes purely declarative — hardware description plus one
constructor call:

```python
broker = eventsys.Broker(
    display_drv=display_drv,
    touch_read=touch_read_func,          # or None: no pointer input
    touch_rotation_table=touch_rotation_table,  # or None: default table
)
```

Inside `Broker.__init__` (sketch):

```python
def __init__(self, display_drv=None, touch_read=None, touch_rotation_table=None,
             *, refresh_period=None, timer_async=False):
    ...existing init...
    if display_drv is not None:
        if touch_read is not None:
            self.touch_dev = self.create(
                type=types.TOUCH, read=touch_read,
                data=display_drv, data2=touch_rotation_table,
            )
        period = refresh_period
        if period is None:
            period = getattr(display_drv, "refresh_ms", None)  # driver policy
        if period:  # only displays that want periodic show()
            self.display_refresh = self.on_tick(
                display_drv.show, period=period, async_=timer_async)
        self.register_quit_cleanup(display_drv, after=self.stop_timer)
```

All parameters default to `None`/off, so `Broker()` with no arguments keeps
working exactly as today (tests, examples, LVGL add-ons, and configs with
non-touch input are unaffected).

Non-touch input (keypad, joystick, encoder, desktop event queues) keeps using
the explicit `broker.create(type=..., read=...)` API — the constructor
parameters are sugar for the overwhelmingly common display+touch case, not a
replacement for the device API.

---

## Worked example: `busdisplay/i80/wt32sc01-plus`

This MCU config (Sunton WT32-SC01 Plus: ESP32-S3, ST7796 320×480 over an I80
parallel bus, FT6x36 capacitive touch on I2C) existed on Jan 1, 2026 and
still exists today, so it shows all three layouts. The hardware-description
half (CPU frequency, shared reset-pin workaround, bus, display, touch chip)
is identical in all three versions and is abbreviated below.

### As of Jan 1, 2026 (`ef14624e`)

```python
from i80bus import I80Bus
from st7796 import ST7796
from machine import I2C, Pin, freq
from ft6x36 import FT6x36
from eventsys import devices

freq(240_000_000)
# Display and touch ICs share reset on pin 4; hold it high here instead of
# letting the display driver toggle it (would knock out the touchscreen).
reset = Pin(4, Pin.OUT, value=1)

display_bus = I80Bus(dc=0, cs=6, wr=47, data=[9, 46, 3, 8, 18, 17, 16, 15])

display_drv = ST7796(display_bus, width=320, height=480, rotation=0,
                     bgr=True, invert=True, backlight_pin=45, ...)

i2c = I2C(0, sda=Pin(6), scl=Pin(5), freq=100000)
touch_drv = FT6x36(i2c)
touch_read_func = touch_drv.get_positions
touch_rotation_table = None

broker = devices.Broker()

touch_dev = broker.create_device(
    type=devices.types.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)
```

Notes: old module layout (`devices.Broker`, `create_device`), no quit
cleanup, and no timer here — bus displays push pixels on draw, and any
refresh timer would have lived *inside* `DisplayDriver` via `auto_refresh`.

### Current (`main` today)

```python
from ft6x36 import FT6x36
from i80bus import I80Bus
from machine import I2C, Pin, freq
from st7796 import ST7796

import eventsys

freq(240_000_000)
reset = Pin(4, Pin.OUT, value=1)  # shared display/touch reset, see note

display_bus = I80Bus(dc=0, cs=6, wr=47, data=[9, 46, 3, 8, 18, 17, 16, 15])

display_drv = ST7796(display_bus, width=320, height=480, rotation=0,
                     bgr=True, invert=True, backlight_pin=45, ...)

i2c = I2C(0, sda=Pin(6), scl=Pin(5), freq=100000)
touch_drv = FT6x36(i2c)
touch_read_func = touch_drv.get_positions
touch_rotation_table = None

broker = eventsys.Broker()

touch_dev = broker.create(
    type=eventsys.TOUCH,
    read=touch_read_func,
    data=display_drv,
    data2=touch_rotation_table,
)

broker.register_quit_cleanup(display_drv)
```

Notes: flat `eventsys` API and quit cleanup, but the input wiring is still
the old shape — the display and rotation table travel through the opaque
`data=`/`data2=` slots, and `data2=None` relies on the reader knowing that
`TouchDevice` substitutes its default rotation table for `None`. Nothing here
says the broker owns the refresh timer; the config simply never mentions
refresh, which is correct for a bus display but indistinguishable from an
accidental omission.

### Proposed

```python
from ft6x36 import FT6x36
from i80bus import I80Bus
from machine import I2C, Pin, freq
from st7796 import ST7796

import eventsys

freq(240_000_000)
reset = Pin(4, Pin.OUT, value=1)  # shared display/touch reset, see note

# 1. bus
display_bus = I80Bus(dc=0, cs=6, wr=47, data=[9, 46, 3, 8, 18, 17, 16, 15])

# 2. display
display_drv = ST7796(display_bus, width=320, height=480, rotation=0,
                     bgr=True, invert=True, backlight_pin=45, ...)

# 3. input device
i2c = I2C(0, sda=Pin(6), scl=Pin(5), freq=100000)
touch_drv = FT6x36(i2c)

# 4. wrapper not needed: FT6x36.get_positions already returns a point list
#    the TouchDevice understands (first point wins), or an empty list.

# 5. touch rotation table: omitted — this panel uses the default table

# 6. broker owns the input device, refresh policy, and quit/timer cleanup
broker = eventsys.Broker(
    display_drv=display_drv,
    touch_read=touch_drv.get_positions,
)
```

The boilerplate `broker.create(... data= ... data2= ...)` block and the
`register_quit_cleanup` call disappear, and "use the default rotation table"
becomes an omitted named parameter instead of an unexplained `data2=None`.
The constructor validates `touch_read` is callable, which the `read=` slot
never did — one currently shipping config,
`busdisplay/spi/diy_esp32_ili9341_xpt2046`, passes
`touch_read_func = (touch_drv.get_touch,)` (a 1-tuple, not a callable) and
would raise `TypeError` on the first poll; verified against the live
`eventsys` code. Named, validated parameters make that class of mistake fail
loudly at import time instead.

For comparison, the desktop config (`board_configs/sdldisplay`) under the
proposal:

```python
display_drv = SDLDisplay(width=320, height=480, rotation=0, scale=2.0, title=...)

broker = eventsys.Broker(display_drv=display_drv)
events_dev = broker.create(type=eventsys.QUEUE, read=get_events, data=display_drv)
```

with `SDLDisplay.refresh_ms = 33` (see displaysys changes) replacing the
hand-written `broker.display_refresh = broker.on_tick(display_drv.show, period=33)`
and `register_quit_cleanup(display_drv, after=broker.stop_timer)` lines.

---

## Changes required in `eventsys`

1. **`Broker.__init__` grows optional parameters**
   `display_drv=None, touch_read=None, touch_rotation_table=None,
   refresh_period=None, timer_async=False` (last two keyword-only).
   Behavior as sketched above. `Broker()` stays valid — no test, example, or
   add-on breaks.
2. **Validation at the boundary.** `touch_read` must be callable;
   `touch_rotation_table`, when given, must be a 4-item sequence. This turns
   silent mis-wiring (the 1-tuple bug) into an immediate, readable error at
   import time of `board_config`.
3. **Refresh wiring only when the display asks for it.** The constructor
   consults `display_drv.refresh_ms` (new displaysys attribute, below) unless
   the caller overrides with `refresh_period`. `refresh_period=0`/`None` plus
   `refresh_ms = None` means "no periodic show" — essential for e-paper
   (periodic full refresh would degrade the panel) and bus displays (draw
   pushes pixels immediately; a 33 ms no-op tick just burns MCU cycles).
4. **Quit cleanup standardized.** When `display_drv` is given, the
   constructor calls `self.register_quit_cleanup(display_drv,
   after=self.stop_timer)`. `stop_timer` is already a safe no-op when no
   timer was started, so this is correct for both timer-using and timer-free
   boards, and fixes the "MCU configs forget `after=stop_timer`" class of bug
   permanently.
5. **Layering stays clean at import level.** `eventsys` continues to *not*
   import `displaysys` (or `multimer`, except lazily in `start_timer`). The
   constructor only duck-types `display_drv` (`show`, `quit`, `rotation`,
   `width`, `height`, optional `refresh_ms`) — the same duck-typing
   `TouchDevice` already relies on via `data=`.
6. **`broker.display_refresh` becomes a real attribute** (initialized to
   `None` in `__init__`) instead of one monkey-patched on by board configs.
   The LVGL takeover protocol in `add_ons/display_driver.py` and
   `tower_climb` keeps working unchanged.
7. **Unaffected:** `broker.create()` for QUEUE/KEYPAD/JOYSTICK/ENCODER,
   `on_tick`/`stop_timer` semantics, `Device` internals, the event classes.

## Changes required in `displaysys`

1. **A per-driver refresh policy attribute**, e.g. `refresh_ms` (class
   attribute, overridable per instance):

   | Driver | `refresh_ms` | Rationale |
   |---|---|---|
   | `SDLDisplay`, `PGDisplay` | `33` | desktop window must be presented periodically |
   | `JNDisplay`, `PSDisplay` | `33` | canvas/notebook must be re-rendered periodically |
   | `FBDisplay` | `None` (default) | dotclock/HUB75 hardware scans the framebuffer out continuously; `refresh()` on demand |
   | `BusDisplay` | `None` | draws push pixels over the bus immediately |
   | `EPaperDisplay` | `None` | refresh is seconds-long and wears the panel; must stay on-demand |
   | `PixelDisplay` | `None` | apps call `show()` after drawing |
   | base `DisplayDriver` | `None` | safe default |

   This is metadata only — **no timer code returns to displaysys**. The
   driver states *what it needs*; the broker decides *how it is driven*.
2. **Nothing else.** `show()`/`deinit()`/`quit()` signatures are already
   what the broker needs (`show(_timer=None)` accepts the tick argument).
   No display gains any knowledge of eventsys or multimer.

## Changes required in `board_configs/`, `src/lib/board_config.py`, tooling

- Regenerate/rewrite the ~135 `board_config.py` files to the 6-step flow
  (53 create input devices today; ~70 are display+broker only, which reduce
  to `broker = eventsys.Broker(display_drv=display_drv)`; 9 CircuitPython
  `displayio`-native configs have no broker and stay as-is).
- Fix the `diy_esp32_ili9341_xpt2046` 1-tuple bug as part of the rewrite.
- Update the generator scripts (`scripts/generate_cp_board_configs.py`,
  `scripts/generate_epaper_board_configs.py`) so regenerated siblings emit
  the new idiom.
- Simplify `src/lib/board_config.py`: `_wire_display_refresh()` collapses
  into the constructor call (`timer_async=True` for PyScript/Jupyter
  branches). `tower_climb`'s `_restore_display_refresh()` re-wires via
  `broker.on_tick` directly instead of importing the helper.
- Update docs: `docs/hardware/board-configs.md`, `docs/concepts/events.md`,
  `docs/concepts/architecture.md`, and the AGENTS.md architecture note.

---

## Pros and cons

### Pros

- **Timer ownership is enforced, not just documented.** Board configs no
  longer contain refresh wiring at all, so a generated or hand-written config
  *cannot* accidentally revert to display-owned timers or forget
  `after=broker.stop_timer`.
- **Less boilerplate, fewer failure modes.** The common display+touch config
  drops from ~10 lines of wiring to 1 constructor call. The opaque
  `data=`/`data2=` slots (which already let a non-callable 1-tuple ship as a
  "read function") are replaced by named, validated parameters.
- **One place to evolve policy.** Refresh period defaults, quit ordering,
  future features (e.g. pausing refresh during heavy blits) change in
  `Broker`, not in 135 files.
- **Generator-friendly.** The other agent's config generation becomes a
  fill-in-the-blanks template; review only needs to check pins and
  calibration, not wiring correctness.
- **Backward compatible.** All parameters are optional; the explicit
  `broker.create`/`on_tick` API remains for keypads, joysticks, encoders,
  desktop event queues, multi-display or multi-touch boards, and tests.

### Cons

- **Conceptual layering blurs slightly.** `eventsys` today is "input devices
  plus a shared timer"; giving `Broker` a `display_drv` parameter makes it a
  board orchestrator. Import-level independence is preserved (duck typing,
  no `import displaysys`), but the docstring story changes. Mitigation: frame
  it as "the broker manages board *lifecycle* (input, ticks, quit); the
  display is one resource it manages."
- **Constructor does invisible work.** A timer may start as a side effect of
  `Broker(...)` (for `refresh_ms` displays). Anyone reading only the board
  config no longer sees the `on_tick` call. Mitigation: `refresh_period=`
  override and clear docs; the previous layout had the same invisibility
  (`auto_refresh=True` inside the driver) with less control.
- **Doesn't cover every input shape.** Keypad/joystick/encoder/queue configs
  still need one `broker.create(...)` call, so the repo carries two idioms.
  This is acceptable: touch is ~80% of input-bearing configs, and the
  remaining device types keep an API that already fits them.
- **One-time churn.** ~126 board configs plus generators, docs, and the
  default `board_config.py` must be regenerated in a single pass, and
  CP/MP sibling pairs must stay in sync. The change itself is mechanical.
- **`refresh_ms` is a new API surface** on displaysys drivers that
  third-party/out-of-tree drivers won't have. The `getattr(...,
  "refresh_ms", None)` lookup makes absence safe (no timer), which is the
  right default for unknown hardware.

### Alternatives considered

- **A separate factory** (`pydisplay.setup(display, touch_read, ...)` or a
  `board_config` helper module) instead of constructor parameters: keeps
  `Broker` pure but adds a new module every config must import, and the
  helper would still poke `broker.display_refresh`/quit internals — more
  moving parts for the same outcome.
- **Displays registering themselves with the broker**
  (`display_drv.attach(broker)`): inverts the dependency the wrong way;
  displaysys would then know about brokers, which the timer refactor
  deliberately removed.

---

## Suggested implementation order

1. `eventsys.Broker` constructor parameters + validation + `display_refresh`
   attribute; unit tests for: no-arg compat, touch device creation, refresh
   wiring on/off by `refresh_ms`, quit cleanup ordering, `refresh_period`
   override, `timer_async`.
2. `displaysys` `refresh_ms` class attributes (+ tests asserting the table
   above).
3. Convert `src/lib/board_config.py` and the four hosted configs
   (`sdldisplay`, `pgdisplay`, `jndisplay`, `psdisplay`); run the example
   matrix headlessly and the LVGL timer kit to confirm the
   `display_refresh` takeover protocol still works.
4. Update generator scripts; regenerate MCU configs; spot-check one config
   per family (busdisplay spi/i80/i2c, fbdisplay, epaperdisplay,
   pixeldisplay) and the Wokwi configs.
5. Docs pass (`docs/hardware/board-configs.md`, concepts pages, AGENTS.md).
