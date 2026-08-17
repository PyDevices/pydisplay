# Run the notebook interactively

The [Jupyter notebook](jupyter-notebook.ipynb) page in these docs is a **static preview** (markdown and code only). To see the live **ipywidgets** display and run touch examples, use Jupyter on your machine.

## Quick start

From a clone of [PyDevices/pydevices-examples](https://github.com/PyDevices/pydevices-examples):

```bash
cd pydevices-examples
python3 -m venv .venv
.venv/bin/pip install pillow ipywidgets ipyevents jupyterlab
.venv/bin/jupyter lab --no-browser
```

Or use the `jupyter.py` CLI runner on PATH (starts JupyterLab and opens a demo):

```bash
jupyter.py calculator
```

Generated demo notebooks are written to `run-{demo}.ipynb` (gitignored).

Open the URL printed in the terminal (for example `http://127.0.0.1:8888/lab/tree/run-calculator.ipynb`) in a browser.

Select the **`.venv`** kernel (**Kernel → Change Kernel**), then run cells top to bottom.

## Requirements

| Package | Purpose |
|---------|---------|
| [Pillow](https://pillow.readthedocs.io/) | Image buffers for `JNDisplay` |
| [ipywidgets](https://ipywidgets.readthedocs.io/en/stable/user_install.html) | Interactive display widget |
| [ipyevents](https://github.com/mwasserman/ipyevents) | Mouse / keyboard on the widget |
| [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html) or [Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/stable/) | Notebook UI in the browser |

No LVGL build is required for the pydevices-examples walkthrough in the notebook.

Desktop `board_config` uses `displaydev.auto.AutoDisplay`, which detects Jupyter (`get_ipython()`) and selects **`JNDisplay`** with `timer_async=True`. The notebook must run with working directory under **`lib/`**. Prefer `PYTHONPATH`/`MICROPYPATH` set to `.:lib:utils` for the kernel process (`jupyter.py` exports it automatically); for fallback when environment variables are unavailable or not set as recommended, see [Utils path setup](../utils.md#path-setup). Either way, resolve example modules with `from examples import <name>` (or `import examples.<a>.<b>` for nested files) — never a bare `import <name>`.

## Touch input

After a cell runs, an **Image** widget appears below the output. **Click that widget** for touch — not the cell chrome and not the static ReadTheDocs page.

`JNDevices` maps mouse events on the widget to the same event API as on hardware. See [Jupyter platform notes](jupyter.md#limitations) for limitations (touch only in the notebook; no encoder emulation).

## VS Code / Cursor

You can run the same notebook in the editor instead of a browser tab:

1. Open the generated notebook (e.g., `run-{demo}.ipynb`).
2. Choose the `.venv` interpreter as the notebook kernel.
3. If the widget area is blank, set [`jupyter.widgetScriptSources`](https://github.com/microsoft/vscode-jupyter/wiki/IPyWidget-Support-in-VS-Code-Python) to load widget JavaScript (this repo’s [`.vscode/settings.json`](https://github.com/PyDevices/pydevices-examples/blob/main/.vscode/settings.json) uses `jsdelivr.com` and `unpkg.com`).
4. Reload the window, restart the kernel, and re-run.

## Stopping background examples

Cells that import **async** examples schedule work with `runtime.run_forever()` / `runtime.run_async(...)` and often return immediately (kernel loop already running). The square **Stop** button often does not cancel them. Use **Kernel → Restart** to stop.

One-shot example cells block until the drawing finishes; **Stop** works there.



## More detail

- [Jupyter platform](jupyter.md) — async execution model, board config, when to use Jupyter vs desktop or PyScript
- [Building docs](../building-docs.md#embedding-the-jupyter-notebook) — why the docs build does not execute the notebook
