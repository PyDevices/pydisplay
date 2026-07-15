# pdwidgets

Cross-platform widget toolkit for pydisplay — now a separate package.

Install from [PyDevices/pdwidgets](https://github.com/PyDevices/pdwidgets):

```python
import mip
mip.install("pdwidgets", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

Documentation: [pdwidgets.readthedocs.io](https://pdwidgets.readthedocs.io)

PyScript widget demos install `pdwidgets` at runtime via `# pyscript mip: pdwidgets` (micropython-lib MIP) or `# pyodide wheels: pdwidgets` (TestPyPI on the Pyodide loader).

## Event loop

Widget apps need a periodic `tick()` to poll events, run tasks, and flush dirty regions to the display.

**Timer mode** (default in most examples) — call before creating the display:

```python
import pdwidgets as pd

pd.init_timer(10)  # tick every 10 ms via multimer
display = pd.Display(board_config.display_drv, board_config.broker)
# ... build UI ...
pd.run_forever()
```

**Poll mode** — omit `init_timer()`; `run_forever()` calls `tick()` in a loop.

See [pdwidgets docs](https://pdwidgets.readthedocs.io) for full API reference.

## Examples

Widget demos remain in `src/examples/widgets_*.py` and `calc_widgets.py` in this repo.

## Icons

Material Design icons ship inside the `pdwidgets` package. See [pdwidgets/icons](https://github.com/PyDevices/pdwidgets/tree/main/src/pdwidgets/icons).
