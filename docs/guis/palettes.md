# palettes

Color palette toolkit for pydisplay — now a separate package.

Install from [PyDevices/palettes](https://github.com/PyDevices/palettes):

```python
import mip
mip.install("palettes", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

Documentation: [palettes.readthedocs.io](https://palettes.readthedocs.io)

PyScript demos install `palettes` at runtime via `# pyscript mip: palettes` (micropython-lib MIP) or `# pyodide wheels: pydevices-palettes` (TestPyPI on the Pyodide loader).

## Usage

```python
from palettes import get_palette

palette = get_palette(name="wheel", length=256, saturation=1.0)
color = palette[42]
```

Palette types: `wheel`, `cube`, `material_design`, and the default Windows-16 named set.

See [palettes docs](https://palettes.readthedocs.io) for full API reference.

## Examples

Palette demos remain in `src/examples/palettes_demo.py`, `graphics_simpletest.py`, `feathers.py`, and others in this repo.
