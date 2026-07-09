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

Use `micropython -i path.py` to test with MicroPython on Unix instead of CPython. Legacy [`hello.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/hello.py) uses the older `tft_config` stack.
