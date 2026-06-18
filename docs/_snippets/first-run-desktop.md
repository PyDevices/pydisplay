From a full clone, after [display dependencies](../guides/desktop-cpython.md#dependencies) are installed:

```bash
git clone https://github.com/PyDevices/pydisplay.git
cd pydisplay/src
python3 -i path.py
```

```python
>>> import hello
```

A window should open with the hello example. Use `micropython -i path.py` to test with MicroPython on Unix instead of CPython.
