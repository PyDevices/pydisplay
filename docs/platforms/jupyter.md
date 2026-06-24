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

Board config: `board_configs/jndisplay/board_config.py` (registers `JNDevices` + `TouchDevice`).

Touch examples (e.g. [`eventsys_touch_test.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/eventsys_touch_test.py)) render a single interactive **ipywidgets Image** — click on that widget.

## Async execution model

The Jupyter board config sets `TIMER_ASYNC = True`. Touch-driven examples use this flag to run an `asyncio` main loop instead of a blocking one, because the notebook kernel already drives an event loop and `ipyevents` callbacks (mouse events) are only delivered when control returns to it.

The example pattern:

- Detect a running loop with `asyncio.get_running_loop()`.
- If one exists (Jupyter, PyScript), schedule the async main coroutine on it with `loop.create_task(...)` and return — the cell finishes immediately while the test continues in the background and streams its output.
- Otherwise (desktop/MCU), fall back to `asyncio.run(...)` or a blocking `run_queued()` + `sleep_ms()` loop.

The wait-for-touch loop yields with `await run_queued()` (from `multimer.aio`) each iteration so the kernel can dispatch widget events between polls. See [multimer](../concepts/multimer.md) for details on the async timer backend.

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
