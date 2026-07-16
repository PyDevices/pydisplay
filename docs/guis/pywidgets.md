# pdwidgets

Cross-platform widget toolkit for pydisplay — now a separate package.

Install from [PyDevices/pdwidgets](https://github.com/PyDevices/pdwidgets):

```python
import mip
mip.install("pdwidgets", index="https://PyDevices.github.io/micropython-lib/mip/PyDevices")
```

Documentation: [pdwidgets.readthedocs.io](https://pdwidgets.readthedocs.io)

PyScript widget demos install `pdwidgets` at runtime via `# deps: pdwidgets` (`?deps=` → MIP on MicroPython / micropip on Pyodide).

## Event loop

`Display` wires into `eventsys.Runtime` at construction (input dispatch and
periodic render ticks). Build the UI, then keep the app alive with
`runtime.run_forever()`:

```python
import board_config
import pdwidgets as pd

display = pd.Display(board_config.display_drv, board_config.runtime)
screen = pd.Screen(display)
# ... build UI ...
board_config.runtime.run_forever()
```

pdwidgets owns no timer of its own — frames are driven from the shared runtime
selected by `runtime.timer_async`. During setup bursts before `run_forever()`,
call `pd.tick()` to flush draws if needed.

See [pdwidgets docs](https://pdwidgets.readthedocs.io) for full API reference.

## Examples

Widget demos live in pydisplay's `src/examples/` — for example
[`widgets_demo.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/widgets_demo.py),
[`widgets_percent.py`](https://github.com/PyDevices/pydisplay/blob/main/src/examples/widgets_percent.py),
and `calc_widgets.py`.

## Icons

Material Design icons ship inside the `pdwidgets` package. See [pdwidgets/icons](https://github.com/PyDevices/pdwidgets/tree/main/src/pdwidgets/icons).
