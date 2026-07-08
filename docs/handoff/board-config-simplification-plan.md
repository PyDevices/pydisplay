# Plan: simplified board_config with broker-constructor wiring

> **Superseded.** This document is historical discussion notes from July 2026.
> The implementation spec is **[Runtime and board_config](../concepts/runtime.md)**.

Status: **proposal / discussion doc** — no code changes yet.
Items marked **DECISION** need sign-off before implementation.

## Goal

Keep the recent architectural decision that **the shared periodic timer is owned
by `eventsys.Broker`**, *not* by display drivers, while making
`board_config.py` files shorter, harder to get wrong, and friendlier to code
generation. The batch-generated MCU configs (busdisplay, fbdisplay,
epaperdisplay, pixeldisplay) predate the broker-timer refactor and follow the
older wiring idioms; rather than hand-porting each one to the current idiom,
this plan proposes a single constructor-based idiom and regenerates everything
once. Since every config is being regenerated anyway, this pass is also the
one chance to fix the `eventsys` vocabulary that appears almost exclusively in
board configs (see [Naming review](#naming-review)).

The proposed canonical flow for every `board_config.py`:

1. Create the bus (if this platform needs one — SPI/I80/I2C, framebuffer, …)
2. Create `display_drv`
3. Create the input device (touch chip, buttons, joystick, …)
4. Create a small wrapper function if the driver doesn't already return what
   the broker expects (e.g. `(x, y)` or `None` for touch)
5. Define the touch rotation table (only when the default table is wrong)
6. Create the broker, passing `display_drv` and the input read function(s) as
   parameters:

```python
# MCU with touch:
broker = eventsys.Broker(
    display_drv=display_drv,
    touch_read=touch_drv.get_positions,
    touch_rotation_table=touch_rotation_table,   # optional
)

# Desktop / hosted (SDL, pygame, PyScript, Jupyter):
broker = eventsys.Broker(
    display_drv=display_drv,
    pump_read=get_events,
)
```

The `Broker` constructor then performs, internally and consistently, what
today has to be hand-written in each config: create the input device(s), wire
periodic display refresh onto the shared timer (only for displays that need
it), and install default quit handling that releases the display and stops
the timer.

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
    touch_read=touch_drv.get_positions,   # or None: no pointer input
    touch_rotation_table=None,            # or omit: default table
)
```

Inside `Broker.__init__` (sketch — names pending the naming review):

```python
DEFAULT_REFRESH_MS = 33   # eventsys owns the default period

def __init__(self, display_drv=None, touch_read=None, touch_rotation_table=None,
             pump_read=None, *, refresh_period=None, timer_async=False):
    ...existing init...
    self.display_refresh = None
    self._timer_async = timer_async
    if display_drv is not None:
        if touch_read is not None:
            self.touch_dev = self.create(
                type=types.TOUCH, read=touch_read,
                data=display_drv, data2=touch_rotation_table,
            )
        if pump_read is not None:
            self.pump_dev = self.create(
                type=types.PUMP, read=pump_read, data=display_drv,
            )
        # Refresh policy: display says IF (bool), eventsys says HOW OFTEN.
        if refresh_period is None:
            wire = getattr(display_drv, "needs_refresh", False)
            period = DEFAULT_REFRESH_MS
        else:
            wire = bool(refresh_period)      # explicit override wins
            period = refresh_period
        if wire:
            self.display_refresh = self.on_tick(
                display_drv.show, period=period, async_=timer_async)
        self._install_default_quit(display_drv)   # implicit; see below
```

All parameters default to `None`/off, so `Broker()` with no arguments keeps
working exactly as today (tests, examples, LVGL add-ons, and configs with
non-touch input are unaffected).

Touch and pump (host event) inputs cover ~85% of input-bearing configs and
are constructor parameters. The remainder (keypad, joystick, encoder) keeps
using the explicit device API — proposed as `broker.add_keypad(read=...)`
etc. in the naming review.

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
proposal shrinks to:

```python
display_drv = SDLDisplay(width=320, height=480, rotation=0, scale=2.0, title=...)

broker = eventsys.Broker(display_drv=display_drv, pump_read=get_events)
```

`SDLDisplay.needs_refresh = True` (see displaysys changes) plus the
eventsys-owned 33 ms default replaces the hand-written
`broker.display_refresh = broker.on_tick(display_drv.show, period=33)`,
`register_quit_cleanup(display_drv, after=broker.stop_timer)`, and
`broker.create(type=eventsys.QUEUE, ...)` lines.

---

## Changes required in `eventsys`

### Constructor parameters

`Broker.__init__` grows optional parameters: `display_drv=None,
touch_read=None, touch_rotation_table=None, pump_read=None`, plus
keyword-only `refresh_period=None, timer_async=False`. Behavior as sketched
above. `Broker()` stays valid — no test, example, or add-on breaks.

Validation at the boundary: `touch_read`/`pump_read` must be callable;
`touch_rotation_table`, when given, must be a 4-item sequence. This turns
silent mis-wiring (the 1-tuple bug) into an immediate, readable error at
import time of `board_config`.

Layering stays clean at import level: `eventsys` continues to *not* import
`displaysys` (or `multimer`, except lazily in the timer start path). The
constructor only duck-types `display_drv` (`show`, `quit`, `rotation`,
`width`, `height`, optional `needs_refresh`) — the same duck-typing
`TouchDevice` already relies on via `data=`.

### Refresh policy: boolean flag, eventsys-owned period

The display driver declares only **whether** it needs periodic presentation —
a True/False class attribute (`needs_refresh`, see displaysys changes). The
**period is owned by eventsys**: a single module-level
`DEFAULT_REFRESH_MS = 33`. Resolution order in the constructor:

1. `refresh_period=<ms>` passed by the board config → wire at that period
   (overrides the display's flag in both directions; `refresh_period=0`
   forces off).
2. Otherwise: wire at `DEFAULT_REFRESH_MS` if `display_drv.needs_refresh`
   is true, else don't wire.

Rationale for the split: whether a backend must be presented periodically is
a property of the *display technology* (an SDL window goes stale; an e-paper
panel is damaged by 30 Hz refresh), but 33 ms is a *policy default* with
nothing display-specific about it. Keeping the number in one place in
eventsys means a future default change (or a power-save mode) touches one
constant, and a board that wants 50 ms says so at the single point where the
board's policy already lives — the `Broker(...)` call.

### Display-refresh claim API

`broker.display_refresh` (the subscription handle) currently works but is a
bare attribute convention with three rough edges: the claimant must know the
`getattr`/`deinit()`/set-`None` sequence; takeover is destructive, so restore
requires re-creating the subscription with knowledge the claimant doesn't own
(`tower_climb._restore_display_refresh()` imports the private
`_wire_display_refresh` from `board_config` to get the period and async flag
back); and nothing expresses exclusive ownership, so two GUI layers could
both "claim."

Because the constructor now retains the refresh spec (callback, period,
async flag), the broker can own the full lifecycle, making release trivial:

```python
claim = broker.claim_display_refresh()   # pause broker-driven show(); return token
...                                      # claimant presents frames itself
claim.release()                          # broker resumes with its own retained spec
```

- **Pause, don't destroy.** Internally a `pause()`/`resume()` on the
  subscription entry (or detach/re-attach of the retained spec). The
  claimant needs zero knowledge to restore; `tower_climb`'s private import
  goes away.
- **Explicit ownership.** A second `claim_display_refresh()` while claimed
  raises (or returns the existing claim — pick one), turning the silent
  double-claim hazard into an error. LVGL's takeover in
  `add_ons/display_driver.py` becomes one line and never releases.
- **Graceful no-op.** On boards with no periodic refresh (bus displays,
  e-paper — most MCU configs) the claim succeeds trivially and `release()`
  does nothing, so GUI-layer code stays portable across board types.
- **Context-manager form** for temporary takeovers:
  `with broker.display_refresh_paused(): ...` is the natural shape for
  `tower_climb`'s claim-during-gameplay pattern, and it is exception-safe,
  which the current manual pair is not.
- **Scope of the promise.** The claim means only "the broker will not call
  `show()` while claimed" — the broker makes no assumption about how the
  claimant presents (LVGL presents from `task_handler` at its own cadence).
- **Compatibility.** `broker.display_refresh` remains as the underlying
  subscription (initialized to `None` in `__init__`), so existing `getattr`
  code keeps working during migration; the claim API is sugar over it.

This also strengthens the case for constructor wiring: the broker retaining
the refresh spec is exactly what makes `release()` trivial.

### Implicit quit handling (retire `register_quit_cleanup` from configs)

Today every config must remember
`broker.register_quit_cleanup(display_drv, after=broker.stop_timer)`. With
`display_drv` known to the constructor, the broker can assume the default:
**on QUIT, stop the shared timer and release the display** — no registration
call needed. The constructor installs it; the `pydisplay_test_mode` escape
hatch moves inside.

What must survive as public surface:

- **A pre-quit hook.** The one real customization in the tree is LVGL
  (`add_ons/display_driver.py`) needing to shut the LVGL event loop down
  *before* the display is released. A single settable hook covers it:
  `broker.before_quit = _lvgl_shutdown` (default `None`). Sequence:
  `before_quit()` → `display_drv.quit()` → stop timer.
- **`broker.on_quit`** can remain as the low-level full-replacement escape
  hatch, or be folded away — with `before_quit` present there is no known
  remaining user. **DECISION:** keep both, or keep only `before_quit`.
  Recommendation: keep only `before_quit`; fewer knobs.
- **`stop_timer()`** disappears from configs entirely. It should remain a
  public method (test kits and teardown code use "stop everything" and it is
  the documented counterpart of `on_tick`), but no generated config will
  ever call it.
- `register_quit_cleanup` itself is deleted (or kept one release as a
  deprecated alias; pre-1.0, deletion is fine since all callers are in-repo
  and regenerated in the same pass).

For brokers constructed *without* a display (bare `Broker()` in tests,
add-ons), QUIT behavior stays as today: nothing beyond `_handle_quit`
dispatch, hooks optional.

### Retire `board_config.TIMER_ASYNC`; ask the broker instead

`TIMER_ASYNC` is a module-level flag in `board_config` consumed by examples
(`dual_main(async_mode=TIMER_ASYNC)`) and `add_ons/display_driver.py`. It
duplicates information the broker already has: which timer flavor drives the
shared tick.

- Constructor: `timer_async=True` is passed by the PyScript/Jupyter branches
  of the default config (they are asyncio-native hosts); everything else
  defaults to sync.
- Broker exposes a read-only property: `broker.timer_async` → `True` if the
  shared timer is (or will be started as) `multimer.AsyncTimer`.
- Consumers change from `from board_config import TIMER_ASYNC` to
  `broker.timer_async`. Grep shows ~12 example files plus
  `display_driver.py`; all mechanical.
- Migration wrinkle: the LVGL timer tests currently *mutate*
  `board_config.TIMER_ASYNC` after import to force a mode. Under the new
  scheme the mode is fixed when the broker is constructed, so those kits
  must select the mode explicitly (they already construct their environment
  deliberately; `tools/lv_timer_test_kit.py` passes the mode through) rather
  than monkey-patching a module global — an improvement, but it must be done
  in the same pass.

### Quit signaling: replace `poll_quit_discarding_others` with a sticky flag

`poll_quit_discarding_others(broker)` was written for one narrow case:
output-only demos (e.g. `displaysys_block_test`) that never read input but
must still close when the SDL/pygame window's X is clicked — the deliberately
awkward name was the warning label. It has since spread to ~26 example files,
including places it was never meant for, and its semantics have drifted:

- Its "discarding" is now only half-true. `Device.poll()` dispatches every
  event to `broker.on(...)`/`on_device(...)` **subscribers** before the
  helper drops the returned list — `testris` gets its joystick input through
  the helper purely via that loophole.
- `tower_climb._wait_for_input` calls it *and* `broker.poll()` in the same
  loop iteration — two drains per pass, so input consumed by the quit-check
  call never reaches the input check (masked only because a tap emits
  multiple events).
- Its real job shrank. QUIT cleanup (release display, stop timer) already
  runs automatically inside any poll via `broker._handle_quit()`; the helper
  contributes only the loop-exit boolean.

Replacement: `broker._handle_quit()` sets `self._quit_requested = True`;
expose read-only **`broker.quit_requested`** (sticky — after QUIT, cleanup
has run and the app should unwind; there is no meaningful un-quit).

- Output-only demos: `while not broker.quit_requested: draw(); broker.poll()`
  — the drain is visible at the call site instead of hidden in a helper.
- Input-reading apps: one drain per iteration, `for ev in broker.poll(): ...`
  plus `if broker.quit_requested: break` — fixes the double-poll pattern by
  construction.
- Checking a flag consumes nothing, so it is safe anywhere, any number of
  times — the entire misuse class disappears. It also composes with the
  future `autopoll()` push mode (a pushed QUIT sets the flag).

`poll_quit_discarding_others` is then deleted (all callers are in-repo and
updated in the same sweep as the `TIMER_ASYNC` removal;
`tests/test_eventsys_quit.py` is rewritten against the flag).

### New idiom enabled by broker-owned timer: push-mode polling

Since the broker owns a periodic timer, it *could* subscribe its own
`poll()` to it and push events to `on()`/`on_device()` subscribers without
the app ever calling `broker.poll()`:

```python
broker.autopoll(period=20)      # or Broker(..., poll_period=20)
broker.on(events.MOUSEBUTTONDOWN, handler)   # fires with no app loop
```

Is it useful? Yes, in two real scenarios:

- **REPL liveliness on MCUs.** Touch/buttons keep working while the user
  sits at the prompt — today input is dead unless something calls `poll()`.
  This is a genuine UX win for the tutorial/demo audience.
- **Purely event-driven apps** (dashboards, kiosk UIs) lose their
  boilerplate `while True: broker.poll(); sleep_ms(1)` loop.

But it must be **opt-in, never default**, because of delivery-context
hazards that mirror the LVGL notes in AGENTS.md:

- On CPython/Linux the sync `multimer.Timer` delivers via a main-thread
  signal handler: subscriber callbacks would interrupt arbitrary user code
  between bytecodes. Callbacks touching non-re-entrant libraries (LVGL,
  pygame) reintroduce exactly the race the refresh-takeover protocol exists
  to avoid.
- On MicroPython hardware timers, callbacks run in ISR context with
  allocation restrictions — polling an I2C touch controller there is not
  viable; delivery would have to bounce through `micropython.schedule`.
- Mixed mode is a foot-gun: if autopoll is active *and* the app also calls
  `poll()`, each event is consumed by whichever poll runs first. Autopoll
  should make direct `poll()` a no-op or an error.

Recommendation: **do not couple this to the current refactor.** Design the
constructor so it doesn't preclude it (it doesn't — the broker owning the
timer is precisely what enables it), note `autopoll()` as follow-up work,
and implement it first for the `AsyncTimer` path where delivery context is
safe (the asyncio event loop), then evaluate the sync/ISR paths.

### Naming review

Context: since all board configs are regenerated in one pass, this is the
cheapest moment ever to fix names. The working interpretation (**confirm**):
the problem names are the eventsys vocabulary that appears almost only in
`board_config.py` files and example boilerplate — `QUEUE`,
`create(type=...)`, `data=`/`data2=`, `touch_read_func`, `TIMER_ASYNC`,
`register_quit_cleanup`, `events_dev`, `poll_quit_discarding_others` — i.e.
wiring jargon that authors must reproduce without it appearing anywhere else
they'd learn it from.

| Current name | Where it appears | Proposal | Notes |
|---|---|---|---|
| `QUEUE` / `QueueDevice` | desktop configs | **`PUMP` / `EventPumpDevice`** | see below |
| `broker.create(type=..., read=..., data=..., data2=...)` | all input configs | constructor params for touch/pump; **`broker.add_keypad(read=)`, `add_joystick(...)`, `add_encoder(...)`** for the rest | kills the `type=` enum and `data`/`data2` at every call site |
| `data=` / `data2=` (Device kwargs) | device construction | real names per device type: touch → `display=`, `rotation_table=`; pump → `display=`, `event_filter=` | base `Device` keeps internal slots; subclasses map named kwargs |
| `touch_read_func` (local var) | MCU configs | `touch_read` or inline `touch_drv.get_positions` | matches the parameter name |
| `TIMER_ASYNC` | board_config export | deleted → `broker.timer_async` | see above |
| `register_quit_cleanup` | all configs | deleted → implicit + `broker.before_quit` | see above |
| `events_dev`, `touch_dev` (exports) | configs | dropped as module exports; available as `broker.touch_dev` / `broker.pump_dev` when needed | shrinks board_config's implicit API |
| `poll_quit_discarding_others(broker)` | ~26 examples | deleted → sticky `broker.quit_requested` property | see "Quit signaling" below |
| `Broker` | everywhere | **DECISION** — keep, or rename (best candidate: `Hub`) | see below |
| `display_drv` (export) | every example | **DECISION** — keep (recommended), or rename to `display` | renaming touches every example, not just configs |

**Is "queue device" the right term?** No. The device wraps the host GUI's
event pump — SDL/pygame/PyScript/Jupyter hand over *fully-formed,
heterogeneous events* (mouse, keyboard, window, quit), unlike raw drivers
(touch, keypad) whose reads return samples the device converts into events.
"Queue" describes the host's internal data structure, not the role. The
standard GUI term for "drain the host's event queue and dispatch" is a
**message/event pump** (Win32 message pump, `pygame.event.pump`), hence
`PUMP` / `EventPumpDevice` / `pump_read=`. Alternative considered: `HOST` /
`HostEventsDevice` (names the origin rather than the mechanism) — fine too;
`PUMP` is shorter and matches the `get_events` read functions the display
backends already export.

**Is "broker" the right term?** Partially. A broker mediates between
producers and consumers, which matches the poll-and-dispatch core. But after
this refactor the object also owns the shared timer, display refresh policy,
and board quit lifecycle — it is the central object everything plugs into,
which is closer to a **hub** than a broker. Renaming is uniquely expensive
for this one name: `broker` is exported by every board_config and used in
every example, test, doc, and add-on. Options:

- Keep `Broker` (zero churn; term is defensible for the pub/sub core).
- Rename to `Hub` in the same pass (most accurate post-refactor; short and
  MCU-friendly; the regeneration covers configs, but examples/docs/add-ons
  are a separate mechanical sweep).

**DECISION** required; the plan is neutral. If renaming, do it in this pass
or never — a second rename later would be worse than either choice now.

Related cleanup worth doing while touching these files: `Broker` currently
*subclasses `Device`* (it is registered as device type `BROKER`). Nothing in
the tree uses a broker as a device; making `Broker` a standalone class
simplifies the mental model ("devices produce events; the broker/hub
dispatches them") and removes the odd `types.BROKER` entry. **DECISION**
(recommended: yes).

### Unaffected

`on_tick` semantics, `Device` internals and event classes, `on()` /
`on_device()` / `subscribe()` dispatch, and `broker.poll()` pull-mode
operation all stay as they are.

## Changes required in `displaysys`

1. **A per-driver boolean**, `needs_refresh` (class attribute, overridable
   per instance). No period lives in displaysys — the period is eventsys's
   `DEFAULT_REFRESH_MS`:

   | Driver | `needs_refresh` | Rationale |
   |---|---|---|
   | `SDLDisplay`, `PGDisplay` | `True` | desktop window must be presented periodically |
   | `JNDisplay`, `PSDisplay` | `True` | canvas/notebook must be re-rendered periodically |
   | `FBDisplay` | `False` (default) | dotclock/HUB75 hardware scans the framebuffer out continuously; `refresh()` on demand |
   | `BusDisplay` | `False` | draws push pixels over the bus immediately |
   | `EPaperDisplay` | `False` | refresh is seconds-long and wears the panel; must stay on-demand |
   | `PixelDisplay` | `False` | apps call `show()` after drawing |
   | base `DisplayDriver` | `False` | safe default |

   This is metadata only — **no timer code returns to displaysys**, and no
   number either. The driver states *whether* it needs periodic
   presentation; eventsys decides *how often* (default) and the board config
   can override (`refresh_period=`). Precedent for the naming style:
   `requires_byteswap`.
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
- Simplify `src/lib/board_config.py`: `_wire_display_refresh()` and the
  `TIMER_ASYNC` export are deleted; the PyScript/Jupyter branches pass
  `timer_async=True` to the constructor. `tower_climb` switches to the claim
  API (`with broker.display_refresh_paused():` or claim/release).
- Decide board_config's canonical export set: **`display_drv` and `broker`
  only** (everything else reachable via the broker). Examples importing
  `TIMER_ASYNC`, `events_dev`, or `touch_dev` are updated in the same pass.
- Update docs: `docs/hardware/board-configs.md`, `docs/concepts/events.md`,
  `docs/concepts/architecture.md`, and the AGENTS.md architecture note.

## Other opportunities in the same pass

Since brokers, eventsys naming, and all board configs are changing together,
these ride along cheaply and should be decided now:

- **Standardize the touch-read contract.** Document exactly what a
  `touch_read` callable may return — `None`/empty for no touch, `(x, y)`,
  `(x, y, ...)`, or a list of points (first wins) — and make wrappers the
  exception. Audit vendored touch drivers against it.
- **Move default rotation tables into touch drivers.** A controller/panel
  combination usually has a known-good table; shipping it as a class
  attribute on the touch driver (e.g. `XPT2046.rotation_table`) would let
  most configs omit step 5 entirely. The `touch_rotation_table=` parameter
  remains the board-level override. **DECISION** (recommended: yes,
  opportunistically — populate where known, don't block on completeness).
- **Manifest-driven config generation.** 58 configs are `cp_*` siblings that
  must not drift from their MicroPython twins. Consider describing each
  board once (pins, controller, touch, bus — TOML/JSON) and generating both
  `board_config.py` variants *and* `package.json` from it. Bigger lift;
  could be a follow-up, but the regeneration pass is when the templates are
  freshest.
- **Release lockstep.** Regenerated configs require the new eventsys;
  configs are MIP-installed from the repo while libraries install from the
  published packages. Regeneration must land in the same release as the
  eventsys/displaysys changes, and `package.json` deps should be checked so
  a new config can't be installed against an old eventsys.
- **Clean up stale tests while there.** `tests/` currently has 14
  pre-existing errors on `main` (constructions passing the removed
  `auto_refresh` kwarg, a `_frame_recorder` attribute regression). The
  eventsys/displaysys test pass should fix these rather than work around
  them.
- **New tests** for: no-arg `Broker()` compat, touch/pump creation and
  validation, refresh wiring on/off via `needs_refresh` and
  `refresh_period`, implicit quit ordering (`before_quit` → display →
  timer), claim/release (including claim-with-no-refresh no-op and double
  claim), `timer_async` property.

---

## Pros and cons

### Pros

- **Timer ownership is enforced, not just documented.** Board configs no
  longer contain refresh wiring at all, so a generated or hand-written config
  *cannot* accidentally revert to display-owned timers or forget teardown.
- **Less boilerplate, fewer failure modes.** The common display+touch config
  drops from ~10 lines of wiring to 1 constructor call; quit handling is
  implicit. The opaque `data=`/`data2=` slots (which already let a
  non-callable 1-tuple ship as a "read function") are replaced by named,
  validated parameters.
- **One place to evolve policy.** Refresh default (one eventsys constant),
  quit ordering, claim semantics, future features change in `Broker`, not in
  135 files.
- **Generator-friendly.** Config generation becomes a fill-in-the-blanks
  template; review only needs to check pins and calibration, not wiring
  correctness.
- **Backward compatible where it matters.** `Broker()` no-arg stays valid;
  `on_tick` and the device API remain for exotic boards, multi-display or
  multi-touch setups, and tests.
- **The claim API closes the last protocol hole**: GUI takeover of
  presentation becomes explicit, restorable, and exception-safe instead of
  an attribute convention plus a private-helper import.

### Cons

- **Conceptual layering blurs slightly.** `eventsys` today is "input devices
  plus a shared timer"; giving `Broker` a `display_drv` parameter makes it a
  board orchestrator. Import-level independence is preserved (duck typing,
  no `import displaysys`), but the docstring story changes — and is part of
  why the `Broker` vs `Hub` naming question is live.
- **Constructor does invisible work.** A timer may start as a side effect of
  `Broker(...)` (for `needs_refresh` displays), and quit handling is
  installed implicitly. Anyone reading only the board config no longer sees
  the wiring. Mitigation: `refresh_period=` override, `before_quit` hook,
  clear docs; the original layout had the same invisibility
  (`auto_refresh=True` inside the driver) with less control.
- **Doesn't cover every input shape.** Keypad/joystick/encoder configs still
  need one `broker.add_*()` call. Acceptable: touch+pump is ~85% of
  input-bearing configs, and the per-type methods are clearer than
  `create(type=...)` anyway.
- **One-time churn, now including examples.** ~126 board configs plus
  generators, the default `board_config.py`, ~12 examples (for
  `TIMER_ASYNC`), docs, and — if `Broker`→`Hub` is chosen — every file that
  says `broker`. All mechanical, but it is a large, coordinated diff and
  CP/MP sibling pairs must stay in sync.
- **`needs_refresh` is a new API surface** on displaysys drivers that
  third-party/out-of-tree drivers won't have. The `getattr(...,
  "needs_refresh", False)` lookup makes absence safe (no timer), which is
  the right default for unknown hardware.

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
- **Per-driver `refresh_ms` numeric attribute** (earlier draft of this
  plan): rejected in favor of the boolean + eventsys-owned default — the
  period is policy, not a display property, and a single constant beats
  seven copies of `33`.

---

## Suggested implementation order

1. Resolve the **DECISION** items: `Broker` vs `Hub`; `QUEUE`→`PUMP` (or
   `HOST`); keep `display_drv` export name or rename; `before_quit` only vs
   also `on_quit`; Broker stops subclassing Device; rotation tables into
   touch drivers.
2. `eventsys`: constructor parameters + validation, `DEFAULT_REFRESH_MS`,
   implicit quit + `before_quit`, `quit_requested` flag (delete
   `poll_quit_discarding_others`), `timer_async` property, claim API,
   renames. Unit tests per the list above; fix the 14 stale test errors.
3. `displaysys`: `needs_refresh` booleans (+ tests asserting the table).
4. Convert `src/lib/board_config.py` and the four hosted configs
   (`sdldisplay`, `pgdisplay`, `jndisplay`, `psdisplay`); update examples
   off `TIMER_ASYNC` and onto `broker.quit_requested`, and `tower_climb`
   onto the claim API (also fixing its double-poll in `_wait_for_input`);
   run the example matrix headlessly and the LVGL timer kit to confirm
   takeover still works.
5. Update generator scripts; regenerate MCU configs; spot-check one config
   per family (busdisplay spi/i80/i2c, fbdisplay, epaperdisplay,
   pixeldisplay) and the Wokwi configs.
6. Docs pass (`docs/hardware/board-configs.md`, concepts pages, AGENTS.md).
7. Follow-ups (not in this pass): `autopoll()` push-mode delivery starting
   with the AsyncTimer path; manifest-driven config generation.
