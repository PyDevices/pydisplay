# PyWidgets (pdwidgets)

Cross-platform widget toolkit in `add_ons/pdwidgets/` — buttons, lists, scrollbars, themes, and more.

## Setup

```python
import lib.path   # dev clone: puts lib/, add_ons/, examples/ on sys.path
```

Install add_ons:

```python
mip.install("github:PyDevices/pydisplay/packages/add_ons.json", target="./add_ons")
```

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

**Poll mode** — omit `init_timer()`; `run_forever()` calls `tick()` in a loop:

```python
# pd.init_timer(10)  # commented out
display = pd.Display(...)
pd.run_forever()
```

**Setup bursts** — during initialization writes before `run_forever()`, call `pd.pump()` each iteration so queued/SDL backends drain timer callbacks and poll-mode apps refresh:

```python
while i < 60:
    console.write(f"{i}\n")
    pd.pump()
pd.run_forever()
```

On queued/SDL backends (CircuitPython SDL, CPython desktop), `Display.refresh()` calls `display_drv.show()` after blitting when `multimer.needs_pump()` is true (same pattern as [`color_setup.py`](https://github.com/PyDevices/pydisplay/blob/main/src/add_ons/color_setup.py)).

On **CPython Linux** (`multimer._ctypes`), `run_forever()` drives `tick()` from the main loop instead of a pdwidgets timer — the module `needs_pump()` flag is true while `Timer.needs_pump()` is false on that backend. Library code checks both flags where relevant.

## Examples

| Script | Description |
|--------|-------------|
| `widgets_demo.py` | Widget showcase |
| `widgets_calc.py` | Calculator UI |
| `widgets_list.py` | List widget |
| `widgets_scrollbar.py` | Scrollbar |
| `widgets_console.py` | Console widget |
| `widgets_percent.py` | Progress/percent |
| `widgets_test.py` | Widget regression demo |
| `widgets_stub.py` | Minimal widget shell |
| `joystick_list_select.py` | List + joystick navigation |
| `console_advanced_demo.py` | Advanced console (mpconsole, not pdwidgets) |

## Icons

Material Design icons converted to `.pbm` in `icons/` — see `icons/README.md` for attribution.

## PyScript note

Themes module has a PyScript workaround (`os.sep` unavailable).
