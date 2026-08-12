# pydevices-examples utils

The files in this folder extend the functionality of pydevices-examples. They are not required for the basic functionality of pydevices-examples, but they can be useful for some applications.  Some of these files are not written by the author of pydevices-examples, but are included here for convenience.  Many of the examples
in the examples folder use these files.

Preferred: set `PYTHONPATH` (CPython) or `MICROPYPATH` (MicroPython/CircuitPython) to `.:lib:utils` and run from `lib/` — no import needed. This package is optional; example scripts never import `utils.path` themselves.

Without those env vars (a bare device REPL, or `boot.py`/`main.py` on a device that keeps `utils/`), set up the path explicitly:

```python
import utils.path  # adds cwd, lib/, and utils/ to sys.path
```

You may instead copy any of the files or directories to a location in your path such as `/lib`.
