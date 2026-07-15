## Summary

Restores pydisplay example matrix compatibility after pdwidgets moved to its own repo.

## Fixes

1. **MicroPython/CircuitPython** — replace keyword-argument `super().__init__(...)` and internal `Widget` / `Icon` / `Label` constructor calls with positional args (`TypeError: function doesn't take keyword arguments`).
2. **CPython 3.12** — simplify `Widget.add_event_cb` signature (no forward-ref `Widget | None` annotation evaluated at class body scope).
3. **`widgets_percent`** — re-export `pct` from `pdwidgets/__init__.py` (`from pdwidgets import pct`).
4. **graphics clip** — import `ClippedCanvas` from `graphics` with `graphics._clip` fallback.
5. **MicroPython** — replace `contextlib.suppress` in spinner/toast with try/except.

## Testing

```bash
PYTHONPATH=tests/stubs:src:<pydisplay>/src/lib python3 -m unittest discover -s tests
```

With pydisplay siblings on path and patches applied, 22/22 palettes+pdwidgets examples pass on CPython and MicroPython (see [pydisplay#78](https://github.com/PyDevices/pydisplay/pull/78)).
