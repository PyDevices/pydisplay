# Run the notebook interactively

The [Jupyter notebook](jupyter-notebook.ipynb) page in these docs is a **static preview** (markdown and code only). To see the live **ipywidgets** display and run touch examples, use Jupyter on your machine.

## Quick start

From a clone of [PyDevices/pydisplay](https://github.com/PyDevices/pydisplay):

```bash
cd pydisplay
python3 -m venv .venv-jupyter
.venv-jupyter/bin/pip install pillow ipywidgets ipyevents jupyterlab
.venv-jupyter/bin/jupyter lab --no-browser
```

Open the URL printed in the terminal (for example `http://127.0.0.1:8888/lab?token=…`) in a browser. In the file browser, open **`src/jupyter_notebook.ipynb`**.

Select the **`.venv-jupyter`** kernel (**Kernel → Change Kernel**), then run cells top to bottom.

## Requirements

| Package | Purpose |
|---------|---------|
| [Pillow](https://pillow.readthedocs.io/) | Image buffers for `JNDisplay` |
| [ipywidgets](https://ipywidgets.readthedocs.io/en/stable/user_install.html) | Interactive display widget |
| [ipyevents](https://github.com/mwasserman/ipyevents) | Mouse / keyboard on the widget |
| [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/getting_started/installation.html) or [Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/stable/) | Notebook UI in the browser |

No LVGL build is required for the pydisplay walkthrough in the notebook.

`src/lib/board_config.py` detects Jupyter (`get_ipython()`) and selects **`JNDisplay`** with `TIMER_ASYNC = True`. The notebook must run with working directory under **`src/`** so `import lib.path` finds `lib/`, `examples/`, and `add_ons/` — opening `src/jupyter_notebook.ipynb` from the repo in JupyterLab does that automatically.

## Touch input

After a cell runs, an **Image** widget appears below the output. **Click that widget** for touch — not the cell chrome and not the static ReadTheDocs page.

`JNDevices` maps mouse events on the widget to the same event API as on hardware. See [Jupyter platform notes](jupyter.md#limitations) for limitations (touch only in the notebook; no encoder emulation).

## VS Code / Cursor

You can run the same notebook in the editor instead of a browser tab:

1. Open `src/jupyter_notebook.ipynb`.
2. Choose the `.venv-jupyter` interpreter as the notebook kernel.
3. If the widget area is blank, set [`jupyter.widgetScriptSources`](https://github.com/microsoft/vscode-jupyter/wiki/IPyWidget-Support-in-VS-Code-Python) to load widget JavaScript (this repo’s [`.vscode/settings.json`](https://github.com/PyDevices/pydisplay/blob/main/.vscode/settings.json) uses `jsdelivr.com` and `unpkg.com`).
4. Reload the window, restart the kernel, and re-run.

## Stopping background examples

Cells that import **async** examples schedule work with `multimer.aio.run()` and return immediately. The square **Stop** button often does not cancel them. Use **Kernel → Restart** to stop.

One-shot example cells block until the drawing finishes; **Stop** works there.

## Download the notebook

On the static [notebook preview page](jupyter-notebook.ipynb), use the **download** button at the top, or open [`src/jupyter_notebook.ipynb`](https://github.com/PyDevices/pydisplay/blob/main/src/jupyter_notebook.ipynb) on GitHub.

## More detail

- [Jupyter platform](jupyter.md) — async execution model, board config, when to use Jupyter vs desktop or PyScript
- [Building docs](../building-docs.md#embedding-the-jupyter-notebook) — why the docs build does not execute the notebook
