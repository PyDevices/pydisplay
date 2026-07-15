# pdwidgets patches for pydisplay sibling setup

Apply when cloning [PyDevices/pdwidgets](https://github.com/PyDevices/pdwidgets) for local example tests:

```bash
PDWIDGETS_SRC="${PYDISPLAY_PDWIDGETS_SRC:-/tmp/pydevices-siblings/pdwidgets}"
patch -p1 -d "$PDWIDGETS_SRC" < patches/pdwidgets/pdwidgets-fixes.patch
```

Or from a pydisplay setup script after clone:

```bash
git clone https://github.com/PyDevices/pdwidgets /tmp/pydevices-siblings/pdwidgets
patch -p1 -d /tmp/pydevices-siblings/pdwidgets < patches/pdwidgets/pdwidgets-fixes.patch
echo "/tmp/pydevices-siblings/pdwidgets/src" > .venv/lib/python*/site-packages/pdwidgets.pth
```

## Fixes included

1. **CPython 3.12+** — remove forward-ref type hint on `Widget.add_event_cb` (MCU-safe).
2. **MicroPython/CircuitPython** — replace keyword-argument `super().__init__(...)` and internal `Widget`/`Icon`/`Label` constructor calls with positional args in `__init__` methods; explicit `PasswordField.__init__` (no `**kwargs`).
3. **`widgets_percent`** — re-export `pct` submodule from `pdwidgets/__init__.py`.
4. **MicroPython** — replace `contextlib.suppress` in spinner/toast with try/except.
5. **graphics clip** — import `ClippedCanvas` from `graphics` with `_clip` fallback.
