From a full clone, after [display dependencies](../guides/desktop-cpython.md#dependencies) are installed:

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
export PYTHONPATH=.:lib:utils
python3 examples/pydisplay_demo.py
```

A window should open with the pydisplay demo (touch or click **Rotate** / **Color**; the tips list scrolls). See the [**pydisplay_demo** guide](../examples/pydisplay_demo.md) for a full walkthrough. To start your own app, copy the [**App starter**](../examples/app-starter.md) boilerplate.

Prefer the REPL? Run `python3 -i` instead and import the demo (never a bare `import pydisplay_demo` — it lives under `examples/`):

```python
>>> from examples import pydisplay_demo
```

Same `PYTHONPATH`, same `cd src`, different interpreter: `micropython examples/pydisplay_demo.py` on Unix MicroPython, `python.exe examples\pydisplay_demo.py` with `set PYTHONPATH=.;lib;utils` on Windows, and `circuitpython examples/pydisplay_demo.py` on CircuitPython Unix.
