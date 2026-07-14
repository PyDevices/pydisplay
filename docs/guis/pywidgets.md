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

**Setup bursts** — during initialization writes before `run_forever()`, call `pd.tick()` each iteration so draws flush to the display:

```python
while i < 60:
    console.write(f"{i}\n")
    pd.tick()
pd.run_forever()
```

`run_forever()` already calls `tick()` each frame. pdwidgets owns no timer of its own — frames are driven cooperatively from the multimer loop selected by `runtime.timer_async`.

## Examples

| Script | Description |
|--------|-------------|
| `widgets_demo.py` | Align enum smoke |
| `calc_widgets.py` | Calculator UI |
| `widgets_percent.py` | Progress/percent |
| `widgets_smartwatch.py` | Showcase: watch face / pages |
| `widgets_settings.py` | Showcase: settings form |
| `joystick_list_select.py` | List + joystick navigation |
| `console_simpletest.py` / `console_advanced_demo.py` | Console demos (`mpconsole`; `pdwidgets.Console` also exists) |

## Icons

Material Design icons converted to `.pbm` in [`assets/icons/`](https://github.com/PyDevices/pydisplay/tree/main/assets/icons) — see [`assets/icons/README.md`](https://github.com/PyDevices/pydisplay/blob/main/assets/icons/README.md) for attribution. Runtime widget icons live under `src/add_ons/pdwidgets/icons/`.

## PyScript note

Themes module has a PyScript workaround (`os.sep` unavailable).
