# Jupyter Notebook

Run pydevices-examples applications in VS Code or Jupyter with the `JNDisplay` backend.

!!! tip "Run it live"
    The [notebook preview](jupyter-notebook.ipynb) on ReadTheDocs is **not interactive**.
    Follow **[Run the notebook interactively](jupyter-run.md)** for JupyterLab or VS Code setup.

!!! note "Read the notebook online"
    [Jupyter notebook](jupyter-notebook.ipynb) shows markdown and code cells only (not executed
    during the build). Use the **download** button on that page, or open
    [`lib/jupyter_notebook.ipynb`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/jupyter_notebook.ipynb)
    from the repo.

## Limitations

- **Touch only** — mouse clicks on the interactive display widget are emulated as touch (`MOUSEBUTTONDOWN`/`MOUSEMOTION`/`MOUSEBUTTONUP`). Keyboard and encoder emulation are not implemented.
- The notebook kernel already runs an `asyncio` event loop, so touch-driven examples must yield to it (see [Async execution model](#async-execution-model)). A blocking poll loop would starve the kernel and never receive widget events.

## Setup

See **[Run the notebook interactively](jupyter-run.md)** for install commands, `./bin/jupyter.sh`, JupyterLab in the browser, and VS Code / Cursor widget settings. Summary:

1. `pip install pillow ipywidgets ipyevents jupyterlab`
2. Open [`lib/jupyter_notebook.ipynb`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/jupyter_notebook.ipynb) from the repo clone, or generate one with `./bin/jupyter.sh <example>`.
3. Run cells top to bottom. `./bin/jupyter.sh` configures pydevices-examples utilities and
   installed or sibling product packages. For fallback path discovery, see
   [Utils path setup](../utils.md#path-setup).

Board config: `pydevices/board_configs/jndisplay/board_config.py`.
It exports the Jupyter display and host reader; `app_runtime` registers the
corresponding host device.

Touch examples (e.g. [`eventsys_touch_test.py`](https://github.com/PyDevices/pydevices-examples/blob/main/lib/examples/eventsys_touch_test.py)) render a single interactive **ipywidgets Image** — click on that widget.

`JNDevices` captures mouse (motion/buttons), wheel, and keyboard input on that Image widget via `ipyevents`. The widget must be focused (clicked) to receive key events, and some keys may be consumed by the notebook front end. Quit uses `JNDisplay.quit_chord` (**Back** / `keys.K_AC_BACK` by default); reassign if the front end intercepts it. See [Displays → How displays expose input](https://pydevices.github.io/pydevices/displaydev.html#how-displays-expose-input).

## Async execution model

The Jupyter board config exports `timer_async=True`; the application coordinator
consumes that preference. Touch-driven examples use `runtime.timer_async` to run
an `asyncio` main loop because the notebook kernel already drives an event loop
and widget callbacks are delivered only when control returns to it.

Examples keep the app alive with **`runtime.run_forever()`** (subscribe callbacks, then run). For a custom async `main()`, use **`runtime.run_async(main)`** rather than `asyncio.run(main())`. On Jupyter the kernel already has a running loop, so `run_async` schedules `main` as a background task and returns immediately (the cell finishes while the coroutine continues). On desktop/MCU with no loop running yet, it blocks via `asyncio.run`. Calling `asyncio.run(main())` directly in a notebook raises `RuntimeError: asyncio.run() cannot be called from a running event loop`.

Custom wait-for-touch loops import `asyncio` from `multimer` and use
`await asyncio.sleep(0)` each iteration so the kernel can dispatch widget
events between polls. See [Runtime](https://pydevices.github.io/pydevices/application-runtime.html) and [multimer](https://pydevices.github.io/pydevices/multimer.html).

## Cursor / VS Code widget rendering

Interactive touch requires ipywidgets JavaScript loaded in the notebook UI. If you see a blank widget box (or a popup about [IPyWidget support](https://github.com/microsoft/vscode-jupyter/wiki/IPyWidget-Support-in-VS-Code-Python)), add this to your workspace or user settings:

```json
"jupyter.widgetScriptSources": ["jsdelivr.com", "unpkg.com"]
```

This repo’s [`.vscode/settings.json`](https://github.com/PyDevices/pydevices-examples/blob/main/.vscode/settings.json) includes that setting. Reload the window after changing it, then restart the kernel.

## Stopping a running example

A touch example scheduled with `create_task` runs as a **background task** on the kernel loop, so the cell itself returns immediately and the **Stop** button won't interrupt it. To stop early, restart the kernel from the kernel picker.

Synchronous, blocking examples (when `runtime.timer_async` is false) keep the cell running; use the square **Stop** button to raise `KeyboardInterrupt`. Such examples should call `sleep_ms(1)` each iteration so Stop can take effect.

## When to use Jupyter

Good for stepping through drawing code and testing touch-driven examples in the notebook. For full keyboard/encoder testing, use [CPython desktop](cpython-desktop.md) or [PyScript](pyscript.md).
