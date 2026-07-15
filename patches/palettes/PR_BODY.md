## Summary

Fixes `get_palette(name="material_design")` on MicroPython and CircuitPython.

MicroPython does not support `strict=True` on `zip()`. `MDPalette._define_named_colors` used `zip(FAMILIES, LENGTHS, strict=True)`, which raised `TypeError: function doesn't take keyword arguments` and broke pydisplay examples such as `calc_graphics` and `palettes_demo` (material step).

## Change

Replace `zip(..., strict=True)` with an explicit length check plus plain `zip(FAMILIES, LENGTHS)`.

## Testing

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

MicroPython smoke:

```bash
micropython -c "import sys; sys.path.insert(0,'src'); from palettes import get_palette; get_palette('material_design')"
```

Paired with [pydisplay#78](https://github.com/PyDevices/pydisplay/pull/78).
