# Jupyter Notebook

Run pydisplay examples in VS Code or Jupyter with the `JNDisplay` backend.

## Limitations

- **Touch only** — mouse clicks on the interactive display widget are emulated as touch (`MOUSEBUTTONDOWN`/`MOUSEMOTION`/`MOUSEBUTTONUP`). Keyboard and encoder emulation are not implemented.
- The notebook kernel already runs an `asyncio` event loop, so touch-driven examples must yield to it (see [Async execution model](#async-execution-model)). A blocking poll loop would starve the kernel and never receive widget events.

## Setup

1. Install Jupyter (VS Code Python + Jupyter extensions, or classic JupyterLab).
2. In your notebook kernel environment:

   ```bash
   pip install pillow ipywidgets ipyevents
   ```

3. Clone the repo or install packages into an environment on the path.
4. Open [`src/jupyter_notebook.ipynb`](https://github.com/PyDevices/pydisplay/blob/main/src/jupyter_notebook.ipynb).
5. Run cells starting with `import lib.path`.

Board config: `board_configs/jndisplay/board_config.py` (registers `JNTouch` as a `TOUCH` device and `JNKeys` as a `QUEUE` device).

Touch examples (e.g. [`eventsys_touch_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/eventsys_touch_test.py)) render a single interactive **ipywidgets Image** — click on that widget.

Keyboard input (`JNKeys`) reuses that same Image widget via `ipyevents`, so the widget must be focused (clicked) to receive key events, and some keys may be consumed by the notebook front end. `JNKeys` also captures an assignable quit chord (default **CTRL+C**) that emits a `QUIT` event; reassign `keys_drv.quit_chord` if the front end intercepts it. See [Displays → How displays expose input](../concepts/displays.md#how-displays-expose-input).

## Async execution model

The Jupyter board config sets `TIMER_ASYNC = True`. Touch-driven examples use this flag to run an `asyncio` main loop instead of a blocking one, because the notebook kernel already drives an event loop and `ipyevents` callbacks (mouse events) are only delivered when control returns to it.

Examples launch their async main coroutine with **`multimer.aio.run(main)`** rather than `asyncio.run(main())`. The helper detects the kernel's already-running loop and schedules `main` with `loop.create_task(...)` (so the cell returns immediately and the coroutine runs in the background), while still blocking to completion on desktop/MCU. This is why calling `asyncio.run(main())` directly in a notebook raises `RuntimeError: asyncio.run() cannot be called from a running event loop`.

The wait-for-touch loop yields with `await run_queued()` (from `multimer.aio`) each iteration so the kernel can dispatch widget events between polls. See [multimer](../concepts/multimer.md#run_queued-and-run-are-optional-helpers) for details on `run()` and the async timer backend.

## Cursor / VS Code widget rendering

Interactive touch requires ipywidgets JavaScript loaded in the notebook UI. If you see a blank widget box (or a popup about [IPyWidget support](https://github.com/microsoft/vscode-jupyter/wiki/IPyWidget-Support-in-VS-Code-Python)), add this to your workspace or user settings:

```json
"jupyter.widgetScriptSources": ["jsdelivr.com", "unpkg.com"]
```

This repo’s [`.vscode/settings.json`](https://github.com/PyDevices/pydisplay/blob/main/.vscode/settings.json) includes that setting. Reload the window after changing it, then restart the kernel.

## Stopping a running example

A touch example scheduled with `create_task` runs as a **background task** on the kernel loop, so the cell itself returns immediately and the **Stop** button won't interrupt it. To stop early, restart the kernel from the kernel picker.

Synchronous, blocking examples (no `TIMER_ASYNC`) keep the cell running; use the square **Stop** button to raise `KeyboardInterrupt`. Such examples should call `sleep_ms(1)` each iteration so Stop can take effect.

## When to use Jupyter

Good for stepping through drawing code and testing touch-driven examples in the notebook. For full keyboard/encoder testing, use [CPython desktop](cpython-desktop.md) or [PyScript](pyscript.md).
