# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""
`pdwidgets`
====================================================
Provides a collection of widgets for creating graphical user interfaces on embedded systems.
It includes base classes for widgets, as well as specific widgets such as buttons, labels, sliders, and more.

Core (always imported): Display, Screen, Task, Widget, themes, constants.

Widgets load lazily via ``__getattr__`` so MCU images only pay for modules you
touch. Lean path::

    from pdwidgets.widgets.button import Button

Convenience::

    import pdwidgets as pd
    pd.Button(...)  # imports widgets.button on first access

See ``WIDGET_DEPS.md`` for the peer import graph.

Optional add-on dependency:
    ``Label`` (and widgets built on it) gains proportional-font rendering when a
    ``font`` module is supplied. That path lazily imports **``add_ons/tft_write``**.

Timer architecture:
    pdwidgets owns **no** timer of its own. Each :class:`Display` wires itself
    into the shared ``eventsys.Runtime`` at construction. Apps build the UI,
    then ``runtime.run_forever()``.
"""

from eventsys import events
from graphics import Area

from ._constants import ALIGN, DEFAULT_PADDING, ICON_SIZE, PAD, POSITION, TEXT_SIZE, TEXT_WIDTH
from ._themes import ColorTheme, IconTheme, get_palette, icon_theme
from .display import Display, tick
from .screen import Screen
from .task import Task
from .widget import Widget

DEBUG = False
MARK_UPDATES = False

# Widget / alias name -> (import path, attribute). Core names live above.
_LAZY = {
    "Accordion": ("pdwidgets.widgets.accordion", "Accordion"),
    "AppBar": ("pdwidgets.widgets.app_bar", "AppBar"),
    "Arc": ("pdwidgets.widgets.gauge", "Arc"),
    "Badge": ("pdwidgets.widgets.badge", "Badge"),
    "BottomSheet": ("pdwidgets.widgets.bottom_sheet", "BottomSheet"),
    "BusyIndicator": ("pdwidgets.widgets.spinner", "BusyIndicator"),
    "Button": ("pdwidgets.widgets.button", "Button"),
    "Card": ("pdwidgets.widgets.card", "Card"),
    "Chart": ("pdwidgets.widgets.chart", "Chart"),
    "CheckBox": ("pdwidgets.widgets.check_box", "CheckBox"),
    "Chip": ("pdwidgets.widgets.chip", "Chip"),
    "ColorPicker": ("pdwidgets.widgets.color_picker", "ColorPicker"),
    "Column": ("pdwidgets.widgets.column", "Column"),
    "ContextMenu": ("pdwidgets.widgets.menu", "ContextMenu"),
    "DatePicker": ("pdwidgets.widgets.date_picker", "DatePicker"),
    "Dialog": ("pdwidgets.widgets.dialog", "Dialog"),
    "DigitalClock": ("pdwidgets.widgets.digital_clock", "DigitalClock"),
    "Divider": ("pdwidgets.widgets.divider", "Divider"),
    "Drawer": ("pdwidgets.widgets.drawer", "Drawer"),
    "Dropdown": ("pdwidgets.widgets.dropdown", "Dropdown"),
    "ExpansionPanel": ("pdwidgets.widgets.accordion", "ExpansionPanel"),
    "Form": ("pdwidgets.widgets.form", "Form"),
    "FormRow": ("pdwidgets.widgets.form_row", "FormRow"),
    "Gauge": ("pdwidgets.widgets.gauge", "Gauge"),
    "Grid": ("pdwidgets.widgets.grid", "Grid"),
    "Icon": ("pdwidgets.widgets.icon", "Icon"),
    "IconButton": ("pdwidgets.widgets.icon_button", "IconButton"),
    "Image": ("pdwidgets.widgets.image", "Image"),
    "Keyboard": ("pdwidgets.widgets.keyboard", "Keyboard"),
    "Label": ("pdwidgets.widgets.label", "Label"),
    "ListTile": ("pdwidgets.widgets.form_row", "ListTile"),
    "ListView": ("pdwidgets.widgets.list_view", "ListView"),
    "Menu": ("pdwidgets.widgets.menu", "Menu"),
    "Navigator": ("pdwidgets.widgets.navigator", "Navigator"),
    "NumberStepper": ("pdwidgets.widgets.number_stepper", "NumberStepper"),
    "Page": ("pdwidgets.widgets.page", "Page"),
    "PasswordField": ("pdwidgets.widgets.password_field", "PasswordField"),
    "PinPad": ("pdwidgets.widgets.pin_pad", "PinPad"),
    "ProgressBar": ("pdwidgets.widgets.progress_bar", "ProgressBar"),
    "RadioButton": ("pdwidgets.widgets.radio_button", "RadioButton"),
    "RadioGroup": ("pdwidgets.widgets.radio_group", "RadioGroup"),
    "Row": ("pdwidgets.widgets.row", "Row"),
    "ScrollBar": ("pdwidgets.widgets.scroll_bar", "ScrollBar"),
    "ScrollView": ("pdwidgets.widgets.scroll_view", "ScrollView"),
    "SegmentedControl": ("pdwidgets.widgets.segmented_control", "SegmentedControl"),
    "Slider": ("pdwidgets.widgets.slider", "Slider"),
    "Spinner": ("pdwidgets.widgets.spinner", "Spinner"),
    "Switch": ("pdwidgets.widgets.switch", "Switch"),
    "TabBar": ("pdwidgets.widgets.tab_view", "TabBar"),
    "TabView": ("pdwidgets.widgets.tab_view", "TabView"),
    "Tag": ("pdwidgets.widgets.chip", "Tag"),
    "TextBox": ("pdwidgets.widgets.text_box", "TextBox"),
    "TextInput": ("pdwidgets.widgets.text_input", "TextInput"),
    "Toast": ("pdwidgets.widgets.toast", "Toast"),
    "Toggle": ("pdwidgets.widgets.toggle", "Toggle"),
    "ToggleButton": ("pdwidgets.widgets.toggle_button", "ToggleButton"),
}

__all__ = [
    "ALIGN",
    "DEBUG",
    "DEFAULT_PADDING",
    "ICON_SIZE",
    "MARK_UPDATES",
    "PAD",
    "POSITION",
    "TEXT_SIZE",
    "TEXT_WIDTH",
    "Area",
    "ColorTheme",
    "Display",
    "IconTheme",
    "Screen",
    "Task",
    "Widget",
    "events",
    "get_palette",
    "icon_theme",
    "tick",
]
__all__ += list(_LAZY.keys())


def __getattr__(name):
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module 'pdwidgets' has no attribute {name!r}")
    mod_path, attr = spec
    mod = __import__(mod_path, None, None, [attr])
    val = getattr(mod, attr)
    globals()[name] = val
    return val


def __dir__():
    return sorted(set(__all__) | set(globals().keys()))
