# App starter

Copy one of the scripts below to start your first pydisplay app. Each is a single file that uses only **`src/lib`** modules — no `add_ons`, no `tft_config`, no `displaybuf`.

| Use this | When you want… |
|----------|----------------|
| **App starter** (this page) | A minimal template: draw the UI, handle clicks, run the recommended main loop |
| **Dual tab** | One file for desktop and PyScript (`dual_main` + `runtime.timer_async`) |
| [**pydisplay_demo**](pydisplay_demo.md) | A feature tour: rotation, hardware scrolling, buffered text, timers |

## Prerequisites

- A working [board config](../hardware/board-configs.md) on your path (from a [full clone](../installation/full-clone.md) or MIP install).
- In a development clone, use `import lib.path` before importing your script so `lib/` and `examples/` are on `sys.path`.

Save the boilerplate as `main.py` (or any name you prefer) and run it from the REPL or as your device's entry point.

## Boilerplate

=== "Sync (queued / sync)"

    Blocking main loop via `multimer.run_forever()`. Use on MCU, desktop CPython, and any port where your app is not asyncio-native.

    ```python
    """
    my_app.py — starting point for a pydisplay app.

    Copy and rename to build your own project. Uses board_config, graphics,
    multimer, and eventsys only.
    """

    import eventsys
    from board_config import display_drv, runtime
    from graphics import Area
    from multimer import run_forever

    # --- customize: colors and layout ---
    BG = 0
    BTN = 0xF800       # red
    BTN_ON = 0x07E0    # green

    button = None
    pressed = False


    def redraw():
        global button
        w, h = display_drv.width, display_drv.height
        display_drv.fill(BG)
        color = BTN_ON if pressed else BTN
        button = Area(display_drv.fill_rect(w // 2 - 50, h // 2 - 25, 100, 50, color))
        display_drv.show()


    def handle_event(e):
        global pressed
        if e.type == eventsys.MOUSEBUTTONDOWN:
            if button.contains(e.pos):
                pressed = not pressed
                redraw()
        # elif e.type == eventsys.KEYDOWN:
        #     ...
        # elif e.type == eventsys.ENCODER:
        #     ...
        # elif e.type == eventsys.QUIT:
        #     return True  # exit main loop if you add a break


    def poll_events():
        if elist := runtime.poll():
            for e in elist:
                handle_event(e)


    def main():
        redraw()
        run_forever(poll_events)


    main()
    ```

=== "Async (asyncio)"

    Asyncio main loop via `multimer.run_forever()`. Use on PyScript or any port where the app already runs under `asyncio` / `uasyncio`. Included in the browser gallery by default; add `# pyscript skip: gallery` to omit or `# pyscript featured` to pin.

    ```python
        """
    my_app_async.py — asyncio starting point for a pydisplay app.

    Copy and rename to build your own project. Uses board_config, graphics,
    multimer, and eventsys only.
    """

    import eventsys
    from board_config import display_drv, runtime
    from graphics import Area
    from multimer import run, run_forever

    # --- customize: colors and layout ---
    BG = 0
    BTN = 0xF800       # red
    BTN_ON = 0x07E0    # green

    button = None
    pressed = False


    def redraw():
        global button
        w, h = display_drv.width, display_drv.height
        display_drv.fill(BG)
        color = BTN_ON if pressed else BTN
        button = Area(display_drv.fill_rect(w // 2 - 50, h // 2 - 25, 100, 50, color))
        display_drv.show()


    def handle_event(e):
        global pressed
        if e.type == eventsys.MOUSEBUTTONDOWN:
            if button.contains(e.pos):
                pressed = not pressed
                redraw()
        # elif e.type == eventsys.KEYDOWN:
        #     ...
        # elif e.type == eventsys.ENCODER:
        #     ...
        # elif e.type == eventsys.QUIT:
        #     return True


    def poll_events():
        if elist := runtime.poll():
            for e in elist:
                handle_event(e)


    async def main():
        redraw()
        await run_forever(poll_events, delay_ms=10)


    run(main)
    ```

=== "Dual (sync + async)"

    One entry file for desktop **and** PyScript. `runtime.timer_async` selects the path; `dual_main()` calls `main_sync()` or schedules `main_async()`. Included in the browser gallery by default; add `# pyscript skip: gallery` to omit or `# pyscript featured` to pin. Pass `async_=runtime.timer_async` to `periodic()` when you add periodic timers.

    ```python
        """
    my_app_dual.py — one file for sync desktop and async PyScript.

    Copy and rename to build your own project. Uses board_config, graphics,
    multimer, multimer, and eventsys only.
    """

    import eventsys
    from board_config import display_drv, runtime
    from graphics import Area
    from multimer import run_forever
    from multimer import dual_main, run_forever as aio_run_forever

    # --- customize: colors and layout ---
    BG = 0
    BTN = 0xF800       # red
    BTN_ON = 0x07E0    # green

    button = None
    pressed = False


    def redraw():
        global button
        w, h = display_drv.width, display_drv.height
        display_drv.fill(BG)
        color = BTN_ON if pressed else BTN
        button = Area(display_drv.fill_rect(w // 2 - 50, h // 2 - 25, 100, 50, color))
        display_drv.show()


    def handle_event(e):
        global pressed
        if e.type == eventsys.MOUSEBUTTONDOWN:
            if button.contains(e.pos):
                pressed = not pressed
                redraw()
        # elif e.type == eventsys.KEYDOWN:
        #     ...
        # elif e.type == eventsys.ENCODER:
        #     ...
        # elif e.type == eventsys.QUIT:
        #     return True


    def poll_events():
        if elist := runtime.poll():
            for e in elist:
                handle_event(e)


    def main_sync():
        redraw()
        run_forever(poll_events)


    async def main_async():
        redraw()
        await aio_run_forever(poll_events, delay_ms=10)


    dual_main(main_sync, main_async, async_mode=runtime.timer_async)
    ```

## Hit testing and `graphics.Area`

The boilerplate imports `Area` from `graphics` **only for hit-testing**. `display_drv.fill_rect(...)` returns an `(x, y, w, h)` tuple; wrapping it in `Area` lets you write `button.contains(e.pos)` instead of inline coordinate math.

`displaysys` and `eventsys` do not depend on `graphics`. If you want a stack with no `graphics` import — or you install only those packages — keep the tuple from `fill_rect` and test clicks directly:

```python
# displaysys + eventsys only — no graphics import
button = None  # (x, y, w, h)


def redraw():
    global button
    w, h = display_drv.width, display_drv.height
    display_drv.fill(BG)
    color = BTN_ON if pressed else BTN
    button = display_drv.fill_rect(w // 2 - 50, h // 2 - 25, 100, 50, color)
    display_drv.show()


def hit(rect, pos):
    x, y, w, h = rect
    px, py = pos
    return x <= px < x + w and y <= py < y + h


def handle_event(e):
    global pressed
    if e.type == eventsys.MOUSEBUTTONDOWN:
        if hit(button, e.pos):
            pressed = not pressed
            redraw()
```

Stick with `from graphics import Area` when you also use rectangle helpers from `graphics` — union (`area1 + area2`), clip, inset, or dirty rects returned by `graphics` draw functions. See [Drawing and fonts](../concepts/drawing-and-fonts.md).

## Run it

From a [full clone](../installation/full-clone.md) with `board_config` on your path, paste the script into `src/main.py` (or run from the REPL):

```python
import lib.path   # adds lib/, examples/ to sys.path (dev clone only)
# import my_app   # or paste/run your saved script
```

Desktop (SDL board config):

```bash
cd src
PYTHONPATH=../board_configs/sdldisplay:lib micropython -i lib/path.py
```

On MCU, install the matching [board config](../hardware/board-configs.md), copy or symlink it as `board_config.py`, and run `main.py` from flash or the REPL.

**Interact:** tap or click the centered rectangle — it toggles between red and green.

## Walkthrough

### `redraw()`

Clears the screen, draws one clickable rectangle, and calls `display_drv.show()` once. `fill_rect` returns `(x, y, w, h)`; the boilerplate wraps that in `Area` for `button.contains(event.pos)`.

Recreate `Area` objects whenever you change layout (same pattern as real apps with moving widgets).

### `handle_event(e)` and `poll_events()`

Per-event handling stays in `handle_event()`. The main loop calls `poll_events()`, which drains `runtime.poll()` and dispatches each event. The starter handles `MOUSEBUTTONDOWN` only. Uncomment the stubs or add branches for keys, encoders, and quit — see [Events](../concepts/events.md).

### Main loop

All three boilerplate tabs use the shared **`run_forever(poll)`** helpers instead of hand-rolled `while True` loops:

| Tab | Helper | Each iteration |
|-----|--------|----------------|
| Sync | `multimer.run_forever(poll_events)` | `poll_events()` → short sleep |
| Async | `await multimer.run_forever(poll_events, delay_ms=10)` | yield to asyncio → `poll_events()` → short sleep |
| Dual | `dual_main(main_sync, main_async, async_mode=runtime.timer_async)` | picks sync or async path from [board config](../hardware/board-configs.md) |

`run_forever` delivers timer callbacks on the active backend — see [multimer](../concepts/multimer.md).

For the **dual** tab, PyScript and Jupyter board configs construct `runtime` with `timer_async=True`; desktop MCU/SDL configs use sync timers. Your app reads `runtime.timer_async` and passes it to `dual_main()` — multimer does not import `board_config`.

To migrate between styles, compare the tabs above or see the sync/async table in [pydisplay_demo → Async variant](pydisplay_demo.md#async-variant).

## Customize

1. **Rename** the file and module docstring; keep the multimer first-line tag accurate if you add timers later.
2. **Layout** — add more `Area` regions, sprites, or shapes in `redraw()`.
3. **Text** — for labels and lists, use `Font` + `FrameBuffer` + `blit_rect` ([Drawing and fonts](../concepts/drawing-and-fonts.md), [`font_simpletest.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/font_simpletest.py)).
4. **Timers** — call `periodic(callback, period=…, async_=runtime.timer_async)` when you need periodic updates (use the **dual** tab pattern); see [multimer](../concepts/multimer.md) and [**pydisplay_demo**](pydisplay_demo.md) for scrolling.

!!! tip "Next steps beyond this template"
    - **Rotation and hardware scroll** — [pydisplay_demo](pydisplay_demo.md)
    - **Event types and runtime** — [Events](../concepts/events.md), [Runtime](../concepts/runtime.md)
    - **All example scripts** — [Examples catalog](index.md)

## Related docs

- [Board configs](../hardware/board-configs.md) — choose and customize `board_config.py`
- [Architecture](../concepts/architecture.md) — how board_config, displaysys, and eventsys fit together
- [pydisplay_demo](pydisplay_demo.md) — flagship feature demo (rotation, scroll, buffered text)
- [Examples catalog](index.md) — full list of scripts
