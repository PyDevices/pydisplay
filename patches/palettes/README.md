# palettes patches for pydisplay sibling setup

Apply when cloning [PyDevices/palettes](https://github.com/PyDevices/palettes) for local example tests:

```bash
PALETTES_SRC="${PYDISPLAY_PALETTES_SRC:-/tmp/pydevices-siblings/palettes}"
patch -p1 -d "$PALETTES_SRC" < patches/palettes/micropython-zip-strict.patch
```

Or use `bash scripts/setup_sibling_repos.sh`.

## Fixes included

1. **MicroPython/CircuitPython** — replace `zip(..., strict=True)` in `material_design.py` with an explicit length check (fixes `calc_graphics` and `palettes_demo` material mode).
