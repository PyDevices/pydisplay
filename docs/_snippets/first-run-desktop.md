From a full clone, after [display dependencies](../guides/desktop-cpython.md#dependencies) are installed:

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
python3 -i lib/path.py
```

```python
>>> import pydisplay_demo
```

A window should open with the pydisplay demo (touch or click **Rotate** / **Color**; the tips list scrolls). See the [**pydisplay_demo** guide](../examples/pydisplay_demo.md) for a full walkthrough. To start your own app, copy the [**App starter**](../examples/app-starter.md) boilerplate.

Use `micropython -i lib/path.py` to test with MicroPython on Unix, 'micropython.exe -i lib\path.py' with MicroPython on Windows and 'circuitpython -i lib/path.py' with CircuitPython on Unix.
