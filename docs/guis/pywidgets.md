# PyWidgets (pdwidgets)

Cross-platform widget toolkit in `add_ons/pdwidgets/` — buttons, lists, scrollbars, themes, and more.

## Setup

```python
import add_ons.add_path   # or install add_ons package
```

Install add_ons:

```python
mip.install("github:PyDevices/pydisplay/packages/add_ons.json", target="./add_ons")
```

## Examples

| Script | Description |
|--------|-------------|
| `widgets_demo.py` | Widget showcase |
| `widgets_calc.py` | Calculator UI |
| `widgets_list.py` | List widget |
| `widgets_scrollbar.py` | Scrollbar |
| `widgets_console.py` | Console widget |
| `widgets_percent.py` | Progress/percent |
| `console_advanced_demo.py` | Advanced console |

## Icons

Material Design icons converted to `.pbm` in `icons/` — see `icons/README.md` for attribution.

## PyScript note

Themes module has a PyScript workaround (`os.sep` unavailable).
