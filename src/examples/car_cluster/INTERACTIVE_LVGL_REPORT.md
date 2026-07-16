# Interactive LVGL / REPL Stability Report

Date: 2026-07-16

This report documents the changes made while stabilizing the LVGL car cluster
under MicroPython unix interactive mode (`micropython -i`). The failure being
fixed was a mix of `micropython.schedule` queue overflow, high CPU / hard
wedges, and LVGL re-entry when keyboard-driven focus/page changes happened
while soft timer callbacks were still being delivered.

The soak harness is not part of the product fix. It lives in:

- `tools/car_cluster_soak.py`
- `tools/car_cluster_soak_worker.py`

## Pre-existing pydisplay source changes

These files existed before the car cluster example work and affect pydisplay
behavior beyond this one example.

### `src/add_ons/display_driver.py`

The temporary `lvgl_event_loop_probe.py` was folded back into `display_driver`.
The `event_loop` class now directly contains the proven pacing behavior:

- LVGL `tick_inc`, `task_handler`, and display `show()` are paced at about
  30 ms (`LVGL_PERIOD_MS = 30`) rather than being run every Runtime service
  tick.
- A wall-clock gate is armed after each LVGL task/flush. If real-time signals
  piled up while LVGL was busy, the next signal cannot immediately run another
  frame back-to-back.
- The Runtime shared timer is still allowed to run at 10 ms. This keeps host
  input and service callbacks responsive while avoiding a 10 ms LVGL render
  cadence.
- `display_driver.main()` subscribes a 10 ms host pump that drains the SDL/HOST
  event path even though LVGL has claimed display refresh and Runtime's normal
  auto-service tick intentionally skips when a GUI layer owns refresh.

Why this was needed:

- In interactive MicroPython, `runtime.run_forever()` returns so the user gets
  the REPL. The app must therefore stay live from timer callbacks alone.
- Running full LVGL task handling every 10 ms made slow frames accumulate
  real-time signal backlog. That could fill `micropython.schedule`, or avoid the
  explicit error but still busy-drain callbacks until the REPL/window wedged.
- Pacing LVGL at the display cadence while keeping host input serviced gives
  the REPL time to accept input and keeps the SDL window responsive.

Future app guidance:

- LVGL applications should not assume the shared Runtime tick period is the
  render period. Let `display_driver.event_loop` own LVGL cadence.
- If an app needs high-rate host input, add lightweight Runtime callbacks or
  host polling; do not raise LVGL `task_handler` frequency to compensate.
- Avoid doing expensive work in the LVGL display tick path. If a frame sometimes
  takes longer than the desired period, the gate should drop/collapse redundant
  frames rather than trying to catch up.

### `src/lib/multimer/_core.py`

Soft timer delivery now coalesces and paces scheduled callbacks:

- Each soft timer keeps at most one scheduled/in-flight callback via
  `_sched_pending`.
- The scheduled callback target is pre-bound (`_deliver_cb`) so the RT-signal
  handler does not allocate a bound method while the heap may be locked.
- `schedule()` failures (`RuntimeError`, including `schedule queue full`) are
  caught and treated as a dropped tick. The next signal can retry.
- Soft callback completion time is tracked. If callbacks take longer than their
  nominal period, subsequent RT-signal deliveries wait for a computed idle gap
  instead of immediately scheduling catch-up work.
- The idle gap is clamped so a timing anomaly cannot disable delivery forever
  while RT signals continue waking the interpreter.

Why this was needed:

- The root problem was not only LVGL. Any slow soft timer callback on a signal
  backend can enqueue faster than the VM drains scheduled work.
- `hard=False` timers should behave like coalescing periodic timers under load,
  not like an unbounded backlog of missed periods.

Future app guidance:

- Timer callbacks should be idempotent per "latest tick" where possible. A
  dropped/coalesced soft tick must not corrupt app state.
- If an app needs every individual event, do not represent it as a high-rate
  periodic soft timer callback. Use an explicit queue with back-pressure.
- Treat `schedule queue full` as a symptom of too much scheduled work, not a
  caller-level exception to paper over.

### `src/lib/eventsys/_runtime.py`

The remaining change is documentation/commentary in `Runtime.run_forever()`:
interactive signal-backed sessions return immediately so the REPL stays usable,
and the comments now point at multimer's soft-timer coalescing/pacing as the
mechanism that prevents LVGL catch-up work from busy-locking the REPL.

No Runtime timer-period bump remains. The Runtime tick can stay at 10 ms; LVGL
render pacing belongs in `display_driver`.

## Car cluster changes from the stability batch

These changes are example-local. They make the car cluster avoid LVGL re-entry
patterns that future LVGL apps should also avoid.

### `src/examples/car_cluster/car_cluster.py`

The example now subscribes a lightweight Runtime `on_tick` callback to drain
pending rail tab changes:

- Rail focus/click callbacks do not call `tabview.set_active()` directly.
- `car_cluster.py` schedules a 30 ms Runtime callback that calls
  `_ui.rails.drain_pending()`.
- This runs outside the LVGL event callback where the rail selection was first
  requested.

Why this was needed:

- The failing sequence was `KEY/FOCUSED/CLICKED -> rails.select() ->
  tabview.set_active()` while LVGL was already inside event/task handling.
- Under MicroPython soft timers, callbacks can also resume while LVGL is
  mid-render. Keeping the tab switch as a deferred action avoids re-entering
  LVGL from inside LVGL.

Future app guidance:

- If an LVGL event handler needs to perform a structural UI change such as
  changing tabs, rebuilding screens, or moving focus groups, prefer deferring
  that action to a Runtime tick or other known-safe phase.
- Event handlers should record intent and update lightweight visual state; the
  larger LVGL mutation can happen later.

### `src/examples/car_cluster/rails.py`

Rails were changed from "select immediately changes the tabview" to
"select records a pending tab and styles the rails":

- `select()` updates rail selection visuals and stores `_pending_tab`.
- `_selecting` guards against recursive focus/click callbacks during selection.
- `drain_pending()` applies `tabview.set_active()` later.
- `drain_pending()` first checks `lv._nesting.value`. If LVGL is already nested,
  it leaves the request pending for a later tick.
- Redundant tab changes are skipped if the tabview is already on the requested
  index.

Why this was needed:

- Calling `tabview.set_active()` from an LVGL `FOCUSED` or `CLICKED` event could
  produce nested focus events and eventually wedge the soft timer path.
- Even when `set_active()` was moved to a Runtime tick, it could still fire
  while `lv._nesting` was non-zero. The nesting guard was the difference between
  intermittent long-run wedges and the passing Enter-key soak.

Future app guidance:

- Treat `lv._nesting.value != 0` as "do not perform broad LVGL tree/navigation
  mutations now".
- Re-entrancy guards around focus/click handlers are cheap insurance, but they
  are not enough by themselves if the handler still performs nested LVGL
  navigation immediately.
- For controls that mirror an external model (selected page, focused mode,
  active route), separate "model/update selected state" from "apply heavy LVGL
  navigation".

## Verification

The final proof run used:

```bash
SOAK_SECONDS=300 SOAK_RUNS=5 SOAK_HB_STALE_S=30 \
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  .venv/bin/python -u tools/car_cluster_soak.py
```

Results:

- 5 runs x 300 seconds passed.
- Each run performed an interactive REPL smoke import first.
- Key injection included arrows, digits, and Enter.
- Final soak logs reported roughly 520-540 injected key events per run.
- No `schedule queue full` errors were found.

Additional checks:

- A separate 300 second soak with `FOCUSED` page switching restored also passed.
- Unit tests were run with `.venv/bin/python -m unittest discover -s tests`.
- Ruff was run against the touched product files. The soak worker keeps
  intentional `E402` path-setup imports because it must run under MicroPython
  from multiple working directories.
