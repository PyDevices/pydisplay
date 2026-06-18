# Jupyter Notebook

Run pydisplay examples in VS Code or Jupyter with the `JNDisplay` backend.

## Limitations

- **No user input yet** — touch, keyboard, and encoder emulation are not implemented for Jupyter.
- Scripts with infinite loops require **Kernel → Restart** (`Ctrl+Shift+P` → "Jupyter: Restart Kernel") to stop.

## Setup

1. Install Jupyter (VS Code Python + Jupyter extensions, or classic JupyterLab).
2. Clone the repo or install packages into a environment on the path.
3. Open [`src/jupyter_notebook.ipynb`](https://github.com/PyDevices/pydisplay/blob/main/src/jupyter_notebook.ipynb).
4. Run cells starting with `import lib.path`.

Board config: `board_configs/jndisplay/board_config.py`.

## When to use Jupyter

Good for stepping through drawing code and inspecting output cells. For interactive input testing, use [CPython desktop](cpython-desktop.md) or [PyScript](pyscript.md) instead.
